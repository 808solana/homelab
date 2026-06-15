# Building Love with a Cursor Agent — Prompt Runbook

This replaces the "run commands yourself on the mini PC" workflow. Now you drive
the build by **pasting prompts into your Cursor agent**, and the agent connects
to the box over Tailscale SSH (user `kor`) and does the install, deploy, and
verification itself. You don't touch the box's terminal.

Drop this file in your home-lab folder next to `USER.md` and your rules. It
assumes those standing rules are already loaded; **Prompt 0** adds the
Love-specific operating contract on top.

---

## How to use this

- Each fenced block below is a prompt. Paste them into the agent **in order**.
- The agent does one milestone per prompt, deploys it, runs the acceptance test,
  pastes the output, and stops. **You review the diff/PR and the test output
  before approving the next prompt.** Autonomy is fine; milestone-boundary review
  is the safety net for a box you're not sitting next to.
- Replace `<HOST>` everywhere with your box's Tailscale address (MagicDNS name or
  `100.x.y.z`). SSH user is `kor`. Project lives at `/mnt/storage/love`.

## Before you start

**Connectivity.** The agent's environment must be able to `ssh kor@<HOST>` and run
`docker` there.
- IDE agent over Remote-SSH from your desktop → Tailscale is already in reach.
- Cloud/background agent → that environment also needs Tailscale (auth key +
  `tailscale up`). If it can't reach the box, Prompt 1's first check fails — if
  that happens, get the Tailscale-in-agent setup sorted before continuing.

**The one secret.** Your OpenRouter key must never land in a prompt, a commit, or
the agent's chat output. Put it in your agent's **secret / env store** as
`OPENROUTER_API_KEY`; Prompt 1 has the agent reference it from the environment
when it writes `.env` on the box. If your agent has no secret store, placing that
one key on the box is the single thing you do by hand.

---

## Prompt 0 — Operating contract (paste once; or add to your `.cursor/rules`)

```
You are building and deploying a service called "Love" to my mini PC. The repo
is here in this workspace; the box is reachable at kor@<HOST> over Tailscale.
Make all file changes in the repo, and all box changes over SSH. Follow this
contract for the whole build:

WORK RHYTHM
- Do ONE milestone per prompt. Implement it, deploy it, run its acceptance test,
  paste the real command output, then summarize and STOP. Do not start the next
  milestone on your own.
- Prefer small, reversible steps. Always show the exact commands you ran on the box.

SCOPE & SAFETY ON THE BOX
- Operate only inside /mnt/storage/love. Do not modify, restart, or remove the
  other containers (Nginx Proxy Manager, Portainer, Cloudflare DDNS) — you may
  read their status only.
- Never run destructive commands: no `rm -rf` outside the project dir, no
  `docker compose down -v`, no `docker system prune`, no overwriting an existing
  .env. If a step needs a clean stop, use `docker compose down` (never -v).
- Deploy with `docker compose up -d --build`. If verification fails, show the
  logs, propose a fix, and pause — don't thrash.

SECRETS
- .env and caches stay gitignored. Never write the real OPENROUTER_API_KEY (or
  any key) into the repo, a commit, a log, or your chat output.
- When creating .env on the box, copy from .env.example and fill secrets from the
  environment (e.g. $OPENROUTER_API_KEY) — do not echo their values. If a required
  key is missing, say which one and pause for me to add it on the box.

GIT
- After each green milestone, commit with a clear message describing what shipped
  and how you verified it.
```

---

## Prompt 1 — M1: scaffold + deploy + verify

```
Milestone 1. Follow the operating contract.

Build the core loop: query -> rules router -> OpenRouter inference -> streamed
answer. No search, no logging yet. A ready-made implementation exists as
love-m1.tar.gz in this workspace — extract that as the source of truth. (If it
isn't present, generate the code to match the behavior below.)

Repo structure:
  app/{main,router,openrouter,love,config}.py, static/index.html,
  Dockerfile, docker-compose.yml, requirements.txt, .env.example, .gitignore, README.md

Behavior:
- FastAPI. POST /api/chat {query}: route the query with keyword rules to one
  model, call OpenRouter's OpenAI-compatible streaming endpoint
  (https://openrouter.ai/api/v1/chat/completions), and stream back Server-Sent
  Events: first a meta frame {type:"meta", model, route, why}, then
  {type:"token", text} frames, then {type:"done"}.
- GET /health returns status + the model map. Serve static/index.html at /.
- Routing rules: coding keywords -> "code"; reasoning/analysis/math keywords ->
  "reasoning"; queries <= 8 words -> "fast"; else "default". Each route maps to a
  model slug read from env. Defaults to verify on openrouter.ai/models:
  code=anthropic/claude-opus-4.6, reasoning=openai/gpt-5,
  fast=google/gemini-2.5-flash, default=google/gemini-2.5-pro. The router returns
  a short human reason ("why this model") shown to the user.
- Prepend a minimal "Love" system prompt to every model call: warm and direct,
  no sycophancy, no flattery, honest even when unwelcome, never fabricates, says
  when uncertain, leads with the real answer.
- The streaming response sets header X-Accel-Buffering: no (so Nginx won't buffer).
- Minimal chat UI: streamed answer, and a badge reading "love chose <model> · <why>".

Deploy: sync the repo to /mnt/storage/love on kor@<HOST>. Create .env from
.env.example, filling OPENROUTER_API_KEY from the environment (don't print it).
Then `docker compose up -d --build`.

Acceptance test — run on the box and paste the output:
  1) curl -s localhost:8000/health
  2) curl -N -X POST localhost:8000/api/chat -H 'content-type: application/json' \
       -d '{"query":"write a python function to reverse a string"}'
  3) docker compose ps
Expected: health is ok; the chat call streams a meta frame naming the CODE model,
then answer tokens; the container is running.

If step 2 returns a 401/auth error, the OpenRouter key isn't set — tell me to add
it to /mnt/storage/love/.env and re-run `docker compose up -d`.

Then report which model the router picked and the first line of the answer, and STOP.
```

After this is green, apply the NPM proxy host (bottom of this file) so it's reachable at your subdomain.

---

## Prompt 2 — M2: real-time search (always-on, with a switch)

```
Milestone 2. Follow the operating contract.

Add a real-time web search step before inference, and feed results to the model.

- Pick a current search/SERP API (e.g. Brave Search API, Tavily, or SerpAPI),
  read its current docs, and add a search module. Its key goes in .env as
  SEARCH_API_KEY (sourced from the environment, never printed).
- For each query: fetch the top N results, pass title+snippet+url into the model
  context, and instruct the model to cite the sources it used.
- Wire a per-request boolean `use_search`, DEFAULT TRUE, threaded end to end.
  Leave it in place even though it's always on now — later Love decides when
  search actually helps, so don't remove the switch.
- UI: render the sources (title + link) under the answer when present, and keep
  the existing model badge.

Acceptance test — paste output:
  - A current-events query (e.g. today's date in the news) returns an answer WITH
    a sources list, and the logs show the search step ran.
Then STOP.
```

---

## Prompt 3 — M3: operative Love + logging

```
Milestone 3. Follow the operating contract.

Make the Love layer do visible work, and make its behavior observable.

- Add SQLite at /mnt/storage/love/data/love.db (gitignored). Log every request:
  query, route, model, searched (bool), latency_ms, and — when the Love layer
  changes the answer — a flag plus a short note on what changed.
- Move Love from a single system prompt to a reshape pass: after the base model
  answers, run a Love check that (a) catches sycophancy / agreement-to-please /
  answers that would steer me wrong, and (b) when the loving answer differs from
  the literal or flattering one, takes the loving path AND logs the override.
- Add a small test set of cases where the loving response differs from the
  flattering/literal one, and assert the system takes the loving path. Make it a
  test I can run.

Acceptance test — paste output:
  - Run the test set: all pass.
  - Show one logged override row from love.db (an answer Love reshaped, with the note).
Then STOP.
```

---

## Prompt 4 — M4: Hermes (observer)

```
Milestone 4. Follow the operating contract.

Create Hermes: a process that watches the whole system from outside the containers.

- Hermes runs NATIVELY on the box (not in a container), owned by kor, as a systemd
  service (or nohup/tmux if systemd isn't suitable). Give it read access to
  love.db and to container logs/stats.
- Note: the Docker socket is root-equivalent on the host. Keep Hermes READ-ONLY
  toward Docker — it observes, it does not control containers.
- Hermes aggregates which model wins on which query type: per-route latency,
  override rate, error rate, volume.

Acceptance test — paste output:
  - Hermes emits a rollup (JSON or Markdown) of per-route model performance built
    from real traffic in love.db.
Then STOP.
```

---

## Prompt 5 — M5: Hermes (learned router)

```
Milestone 5. Follow the operating contract.

Use Hermes's data to replace the keyword rules with learned routing.

- Train a lightweight classifier on the accumulated data to predict the best
  route/model for a new query.
- Run it in SHADOW MODE first: for each live query, log the learned router's
  choice next to the keyword rules' choice, without changing what actually runs.
- Expose a flag to switch live routing from rules -> learned once shadow results
  look good. Keep the keyword rules as a fallback.

Acceptance test — paste output:
  - Shadow-mode comparison over recent traffic: where learned and rules agree /
    disagree, and the disagreements worth a look.
Then STOP.
```

---

## Applying the NPM proxy host (one UI step, after M1)

The agent can't safely edit Nginx Proxy Manager's database, so do this once in the
NPM web UI:

- **Proxy Host** → Domain `love.korgems.com` → forward to the Love container on
  port `8000` (scheme http; host = the container name if NPM shares its Docker
  network, otherwise the box's IP).
- **Websockets Support:** on.
- **SSL:** request a Let's Encrypt cert, Force SSL.
- **Advanced** tab: add `proxy_buffering off;` — without it Nginx buffers the
  stream and the answer arrives all at once instead of token by token.

---

## Update your project instructions

The agent-driven workflow makes the old per-command rule obsolete. In your project
instructions, replace the "propose commands and wait for my approval per command"
bullet with:

- The Cursor agent builds and deploys to the box over Tailscale SSH (`kor@<HOST>`).
  I don't run commands on the box by hand.
- The agent works one milestone per prompt, deploys, runs the acceptance test, and
  stops; I review the diff and the test output before approving the next milestone.
- Guardrails live in the agent's operating contract: project dir only, no
  destructive commands, secrets sourced from the environment and never committed.
```
