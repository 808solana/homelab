# Love — M1

A self-hosted multi-model answer engine. M1 proves the core loop:

```
query  ->  rules router  ->  OpenRouter inference  ->  streamed answer
```

Love picks the model that fits the query, calls it through OpenRouter, streams
the answer back, and tells you which model it chose and why. Real-time search,
decision logging, and the full Love reshape pass are later milestones.

## Files

```
love/
├── docker-compose.yml      # one service, env-driven
├── Dockerfile
├── requirements.txt
├── .env.example            # copy to .env, add your OpenRouter key
├── app/
│   ├── main.py             # FastAPI: /api/chat (SSE stream), /health, UI
│   ├── router.py           # rules-based routing (v1 of Love's routing brain)
│   ├── openrouter.py       # streaming OpenRouter client
│   ├── love.py             # the Love character system prompt (v1)
│   └── config.py           # env config + the model routing table
└── static/
    └── index.html          # minimal chat UI, streamed, with model attribution
```

## Run it (on the N100, as user `kor`)

```bash
mkdir -p /mnt/storage/love && cd /mnt/storage/love
# put these files here (git clone, scp, or sync from Cursor)

cp .env.example .env
nano .env                       # paste your OpenRouter key; confirm model slugs

docker compose up -d --build
docker compose logs -f love     # watch it boot
```

Smoke test from the box:

```bash
curl -s localhost:8000/health
curl -N -X POST localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"query":"write a python function to reverse a string"}'
```

Then in Nginx Proxy Manager: add a proxy host (e.g. `love.korgems.com`) →
the container on port 8000. Enable **Websockets Support**, and in **Advanced**
add `proxy_buffering off;` so the streamed answer isn't buffered. Request a
Let's Encrypt cert.

## Routing (current rules)

| route       | when                                   | model (default)              |
|-------------|----------------------------------------|------------------------------|
| `code`      | coding keywords                        | `anthropic/claude-opus-4.6`  |
| `reasoning` | reasoning / analysis / math keywords   | `openai/gpt-5`               |
| `fast`      | short, simple queries (≤ 8 words)      | `google/gemini-2.5-flash`    |
| `default`   | everything else                        | `google/gemini-2.5-pro`      |

Swap any slug in `.env` — no code change. Verify slugs at
https://openrouter.ai/models.
