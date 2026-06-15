# Agent Instructions

## Purpose
This workspace manages a personal homelab: a Windows desktop workstation
and a Debian mini-PC running self-hosted services.

## Behaviour Rules
- Always show me the commands you intend to run BEFORE executing them.
- Never modify files outside this workspace without explicit confirmation.
- Never store credentials in any committed file. Read from `.env` (gitignored).
- When connecting to the Debian server, use SSH key auth, not passwords.
- Before changing anything on the Debian server, snapshot or back up first.
- For any destructive action (delete, drop, rm -rf, format, reformat disks,
  replacing a kernel, etc.), require me to type "CONFIRM" before proceeding.
- Reference `homelab.md` for infrastructure context. Update it whenever
  the architecture changes.

## Allowed Tools
- File reads/writes inside this workspace
- Shell commands (PowerShell locally, bash on remote) — WITH my approval
- SSH to documented hosts in homelab.md
- Docker / docker compose commands
- Git operations on this repo

## Disallowed Without Explicit Approval
- Changes to router configuration
- Anything touching production data on services already in use
- Installing kernels or hypervisors (this includes Proxmox)
- Disabling firewalls
- Opening ports on the router
