# Scaling Plan: Multi-Client Hosting on One Server

## Current Structure (Observed)

- The project is currently single-tenant:
  - one frontend
  - one backend
  - one proxy
  - one Redis
  - one Postgres
  - all inside one Docker Compose stack.
- TLS/routing is configured for one host in the proxy config.
- Backend CORS currently allows only one `FRONTEND_URL`.
- Production deployment docs are also oriented around one domain/one stack.

## Target Architecture

Goal: host multiple clients on one server with subdomains, each possibly using a totally different codebase.

Example:
- `client1.webshop.fr`
- `client2.webshop.fr`

Recommended model:
- One **shared edge reverse proxy** (Traefik or Caddy recommended) on ports 80/443.
- One **independent Docker Compose project per client**.
- Routing by Host header:
  - `client1.webshop.fr` → client1 services
  - `client2.webshop.fr` → client2 services
- Automatic TLS certificates per subdomain (or wildcard cert via DNS challenge).

## Recommended Server Layout

- `/srv/platform/proxy` → shared reverse proxy stack only
- `/srv/clients/client1` → client1 repo + compose + env + secrets + data
- `/srv/clients/client2` → client2 repo + compose + env + secrets + data

Each client stack should:
- join one shared external Docker network used by the edge proxy
- keep app/db/cache networks and volumes private to that client

## Isolation Rules (Important)

- Do not share databases between clients.
- Use unique compose project names and container names per client.
- Keep per-client secrets, backups, logs, and monitoring.
- Enforce per-client CPU/RAM limits to avoid noisy-neighbor issues.
- Remove single-domain assumptions from app config (CORS, callback URLs, env vars).

## Migration Path from Current Setup

1. Extract proxy into a dedicated shared proxy project.
2. Convert current WebShop into first tenant stack (`client1`) with isolated DB/Redis/secrets.
3. Update backend CORS to support an allowlist of client domains (instead of one `FRONTEND_URL`).
4. Add `client2` as a separate compose project and host rule.
5. Set up independent CI/CD deployment per client.

## Operational Notes

- DNS: point each subdomain (`clientX.webshop.fr`) to the same server IP.
- SSL: automate cert issuance/renewal at the shared proxy layer.
- Backups: schedule DB + volume backups per client.
- Rollback: maintain per-client release history to roll back one client without impacting others.

## Next Practical Step

Create a production-ready scaffold with:
- one shared proxy stack
- one template client stack
- host-based routing rules for `client1.webshop.fr` and `client2.webshop.fr`
- checklist for adding future clients in <10 minutes.
