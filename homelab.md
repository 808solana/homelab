# Homelab Architecture

## Overview
Two-node homelab: Windows workstation + Debian mini-PC.

## Workstation: Windows Desktop
- OS: Windows 11
- CPU: AMD Ryzen 5 (6-series)
- GPU: NVIDIA RTX 3060
- RAM: 32 GB
- Storage: ~1 TB
- Role: Daily driver, dev environment, Cursor agent host

## Server: Debian Mini-PC
- OS: Debian GNU/Linux 13 (trixie), version 13.5
- Kernel: 6.12.88+deb13-amd64 (x86-64)
- Hardware: Trigkey "Key Mini", Intel N100 (4 cores), 16 GB RAM, ~900 GB NVMe
- Hostname: kor
- IP (LAN): 192.168.0.150 (on wlo1 / Wi-Fi; wired enp1s0 is DOWN)
- IP (Tailscale): see `.env` (DEBIAN_SSH_HOST)
- Uptime at audit: 6 days
- Role: Self-hosting platform
- Runtime: Docker Engine 29.5.0 (Community) + Docker Compose v5.1.3 + Portainer CE
- Public domain: korgems.com
  - u.korgems.com — noVNC-based Linux remote desktop

### Storage
Two physical disks:
- **nvme0n1** — Samsung SSD 990 PRO 1TB (931.5 GB). OS + Docker data.
  - `nvme0n1p1` 976M vfat → `/boot/efi`
  - `nvme0n1p2` 56.8G ext4 → `/` (~64% used)
  - `nvme0n1p3` 15.8G swap
  - `nvme0n1p4` 858G ext4 → `/home` (~801 GB free)
- **sda** — "512GB SSD" (476.9 GB), formerly an old Windows disk. Wiped 2026-05-28
  and repurposed as a second Linux drive.
  - `sda1` ext4 → `/mnt/storage` (469 GB usable, owned by `kor:kor`)
  - fstab UUID see server; mounted with `nofail` (boot-safe on this remote box)
  - fstab backup at `/etc/fstab.bak`

### Docker Compose Projects (from `docker compose ls`)
| Project | Status | Compose file |
|---|---|---|
| nginx-proxy-manager-stack | running | /data/compose/1/docker-compose.yml |
| cloudflare | running | /data/compose/10/docker-compose.yml |
| uuuuuu | running | /data/compose/97/docker-compose.yml |
| u2 | paused | /data/compose/101/docker-compose.yml |
| u3_desktop1 | paused | /data/compose/103/docker-compose.yml |
| u4_d2 | paused | /data/compose/104/docker-compose.yml |
| onestopsold | paused | /data/compose/105/docker-compose.yml |

### Containers (10 total: 4 running, 4 paused, 2 stopped)
- **portainer** (portainer/portainer-ce) — ports 8000, 9443 — Docker management UI
- **nginx-proxy-manager-stack-app-1** (jc21/nginx-proxy-manager) — ports 80, 81 (admin UI), 443 — reverse proxy
- **cloudflare-cloudflare-ddns-1** (oznu/cloudflare-ddns) — dynamic DNS updater for Cloudflare
- **ubuntu-novnc-desktop** (dorowu/ubuntu-desktop-lxde-vnc) — ports 6080 (noVNC/web), 5900 (VNC) — healthy; primary desktop behind u.korgems.com
- **ubuntu-desktop-2 / u4_d2 / ubuntu-desktop-1** (dorowu/ubuntu-desktop-lxde-vnc) — noVNC 6081/6082/6083, VNC 5901/5902/5903 — currently **paused**
- **onestopsold-web** (onestopsold-onestopsold) — port 3001 — web app, currently **paused**
- **korgems-web** (pleasework-korgems) — **exited** (stopped 4 months ago)
- **terminal** (ubuntu:latest) — **exited** (stopped 3 weeks ago)

### Reverse Proxy
- Nginx Proxy Manager (NPM), container `nginx-proxy-manager-stack-app-1`
- Listens on host ports 80 (HTTP), 443 (HTTPS), 81 (admin web UI)
- Routes public domain traffic (korgems.com / u.korgems.com) to internal containers

### Listening Ports (host)
- 22 — SSH
- 80, 443 — NPM (HTTP/HTTPS)
- 81 — NPM admin UI
- 8000, 9443 — Portainer
- 3001 — onestopsold-web
- 5900-5903 — VNC (desktop containers)
- 6080-6083 — noVNC web (desktop containers)
- 41641/udp — Tailscale

## Network
- LAN subnet: 192.168.0.0/24
- Default gateway: 192.168.0.1
- Server LAN address: 192.168.0.150 (Wi-Fi, wlo1)
- Remote access: Tailscale (tailscale0, see `.env` for IP)
- Public access: via Nginx Proxy Manager reverse proxy + Cloudflare (DDNS via oznu/cloudflare-ddns)
- Router: TBD model, TBD management approach

## Credentials & Secrets
NEVER stored in this file. See `.env` (gitignored) for:
- DEBIAN_SSH_HOST
- DEBIAN_SSH_USER
- DEBIAN_SSH_KEY_PATH

## Access Notes
- SSH: key auth as `kor` (key path in `.env`).
- **TEMPORARY:** passwordless sudo enabled via `/etc/sudoers.d/99-kor-nopasswd`
  (added 2026-05-28 so the agent can run sudo non-interactively).
  **TODO: remove or scope when homelab work is done** — `sudo rm /etc/sudoers.d/99-kor-nopasswd`.

## Backup & Recovery
- TBD — establish a tested backup BEFORE any major changes
- Note: compose files live under /data/compose/<id>/ (Portainer-managed stacks)
- Docker volumes present: portainer_data, u2_ubuntu_desktop_2, uuuuuu_ubuntu-desktop-data
- New `/mnt/storage` (469 GB) and `/home` (~801 GB free) are candidate backup targets

## Open Questions / To Verify
- Which exact subdomains are mapped in NPM, and to which containers/ports
- Cloudflare DDNS: which domain/zone it updates
- The "uuuuuu" running project — what it serves (likely a noVNC desktop; volume uuuuuu_ubuntu-desktop-data)
- Whether paused desktops/onestopsold should be running or cleaned up
- Router model and management approach
