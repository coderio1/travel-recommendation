# Travel Recommendation System

FastAPI + PostgreSQL travel-recommendation app behind a **Traefik** reverse proxy
with automatic Let's Encrypt TLS.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic v2
- **Database:** PostgreSQL 16
- **Auth:** JWT (HS256) + bcrypt
- **Reverse proxy:** Traefik v3.7 (HTTP→HTTPS redirect, Let's Encrypt, security headers, dashboard)
- **Frontend:** Vanilla HTML/CSS/JS served by FastAPI
- **Infra:** Docker + Docker Compose

## Architecture

```
Browser ──HTTPS:443──> Traefik ──HTTP:8000──> backend ──TCP:5432──> db
              :80 (redirected to :443)                     (internal network only)
```

Only Traefik publishes ports to the host. The backend and database are
reachable only inside the Docker network.

## Project layout

```
.
├── docker-compose.yml          Orchestrates traefik + db + backend
├── env-example                 Copy to .env and edit
├── run_after_env_setup.sh      Run in CLI after .env setup
├── traefik/
│   ├── traefik.yml             Static Traefik config (entrypoints, ACME resolvers)
│   └── traefik_dynamic.yml     Dynamic Traefik config
├── postgres/init/              SQL run on first DB boot
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    └── app/                    FastAPI application (see /docs after start)
```

## Prerequisites
Installed: 
- docker
- mkcert


## First-time setup - Localhost run

### 1. Configure environment

```bash
cp env.example .env
nano .env    # or your editor of choice
```

You **must** set:
- `ACME_EMAIL` — your real email (Let's Encrypt sends expiry notices here)
- `JWT_SECRET` — generate with `openssl rand -hex 32`
- `TRAEFIK_DASHBOARD_AUTH` — see below

Generate the dashboard basic-auth string:
```bash
docker run --rm httpd:2.4-alpine htpasswd -nbB admin 'your-strong-password' \
    | sed -e 's/\$/\$\$/g'
```
Paste the result as `TRAEFIK_DASHBOARD_AUTH=...` in `.env`.

### 2. Run bash script in your terminal

```bash
./run_after_env_setup.sh
```

## 3. Open dashboards in the browser

#### Traefik ####
`https://traefik.your.domain/dashboard/`

#### Application ####
`https://your.domain`

