# Travel Recommendation System

A full-stack travel recommendation web app. Users register, describe their travel preferences (destination, activity type, budget, travel window), and receive a ranked list of matching destinations with the option to save favourites.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | JWT (HS256) + bcrypt |
| Frontend | Vanilla HTML/CSS/JS (served by FastAPI) |
| Reverse proxy | Traefik v3.7 — HTTP→HTTPS redirect, Let's Encrypt TLS, security headers |
| Infrastructure | Docker + Docker Compose |

## Architecture

```
Browser ──HTTPS:443──▶ Traefik ──HTTP:8000──▶ backend ──TCP:5432──▶ db
              :80 (redirected to :443)                (internal network only)
```

Only Traefik exposes ports to the host. The backend and database are reachable only inside the `travel_net` Docker network.

## Project Structure

```
.
├── docker-compose.yml              # Orchestrates traefik + db + backend
├── env-example                     # Copy this to .env and fill in your values
├── run_before_docker_containers.sh # Creates required external Docker volumes
├── traefik/
│   ├── traefik.yml                 # Static Traefik config (entrypoints, ACME)
│   ├── traefik_dynamic.yml         # Dynamic Traefik config
│   ├── acme.json                   # Let's Encrypt cert storage (must be chmod 600)
│   └── cert/                       # Local self-signed cert for dev
├── postgres/
│   ├── init/                       # SQL files run on first DB boot
│   │   ├── 01-schema.sql
│   │   └── 02-seed.sql
│   └── migrations/                 # Incremental schema changes
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py                 # FastAPI app entry point, routers, CORS, static files
        ├── config.py
        ├── database.py
        ├── deps.py                 # Shared FastAPI dependencies (DB session, current user)
        ├── security.py             # JWT creation and verification
        ├── crud/                   # Database access layer
        ├── models/                 # SQLAlchemy ORM models
        ├── routers/                # FastAPI route handlers
        ├── schemas/                # Pydantic request/response schemas
        ├── services/
        │   └── recommender.py      # Scoring engine
        └── static/                 # SPA frontend (index.html, app.js, style.css)
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health` | — | Health check |
| `POST` | `/api/auth/register` | — | Register a new user |
| `POST` | `/api/auth/login` | — | Login, returns JWT |
| `GET` | `/api/destinations` | ✓ | List all destinations |
| `GET` | `/api/activities` | ✓ | List all activity types |
| `POST` | `/api/recommendations` | ✓ | Generate ranked recommendations |
| `GET` | `/api/recommendations/{id}` | ✓ | Retrieve a past recommendation |
| `GET` | `/api/recommendations` | ✓ | List your recommendation history |
| `GET` | `/api/favorites` | ✓ | List your saved favourites |
| `POST` | `/api/favorites` | ✓ | Save a result to favourites |
| `DELETE` | `/api/favorites/{id}` | ✓ | Remove a favourite |

Interactive API docs (Swagger UI) are available at `/docs` when the app is running (basic-auth protected in production).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin

## Setup

### 1. Configure environment

```bash
cp env-example .env
```

Open `.env` and set the required values:

| Variable | Description |
|----------|-------------|
| `DOMAIN` | Your domain (e.g. `example.com`) |
| `ACME_EMAIL` | Real email address for Let's Encrypt expiry notices |
| `CERT_RESOLVER` | Start with `letsencrypt-staging`; switch to `letsencrypt` after verifying |
| `TRAEFIK_DASHBOARD_AUTH` | bcrypt basic-auth string — see generation command below |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `JWT_SECRET` | Random secret — see generation command below |

**Generate JWT secret:**
```bash
openssl rand -hex 32
```

**Generate Traefik dashboard auth string:**
```bash
docker run --rm httpd:2.4-alpine htpasswd -nbB admin 'your-strong-password' \
    | sed -e 's/\$/\$\$/g'
```
Paste the output as `TRAEFIK_DASHBOARD_AUTH=...` in `.env`.

### 2. Create external Docker volumes

```bash
./run_before_docker_containers.sh
```

### 3. Verify `acme.json` permissions

Traefik refuses to start if this file is not `chmod 600`:

```bash
chmod 600 traefik/acme.json
```

### 4. Start the stack

```bash
docker compose up -d --build
docker compose logs -f
```

The app will be available at `https://www.your-domain.com`

## DNS Requirements

For Let's Encrypt certificates to be issued, your server's public IP must be reachable on ports 80 and 443, and DNS must point to it:

| Record | Type | Value |
|--------|------|-------|
| `yourdomain.com` | A | `<server-public-ip>` |
| `www.yourdomain.com` | A | `<server-public-ip>` |
| `traefik.yourdomain.com` | A | `<server-public-ip>` *(optional, for the dashboard)* |

Without these records, Let's Encrypt's HTTP-01 challenge will fail. Use `letsencrypt-staging` first to validate the setup without hitting rate limits.

## Switching to Production Certificates

Once staging works (you see the app at `https://www.yourdomain.com`, even with a browser warning):

1. Set `CERT_RESOLVER=letsencrypt` in `.env`
2. Wipe the staging cert and restart:

```bash
docker compose down
echo '{}' > traefik/acme.json && chmod 600 traefik/acme.json
docker compose up -d --build
```

## Useful Operations

```bash
# Watch all logs
docker compose logs -f

# Traefik logs only
docker compose logs -f traefik

# Reload after label changes (no rebuild needed)
docker compose up -d

# Reset everything including the database
docker compose down -v
echo '{}' > traefik/acme.json && chmod 600 traefik/acme.json
docker compose up -d --build
```

## Quick API Test

```bash
# Register
curl -X POST https://www.yourdomain.com/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"[email protected]","name":"name","password":"securepassword"}'

# Login and capture the JWT
TOKEN=$(curl -s -X POST https://www.yourdomain.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"[email protected]","password":"securepassword"}' \
    | jq -r .access_token)

# Get a recommendation
curl -X POST https://www.yourdomain.com/api/recommendations \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "wanted_country": "Italy",
        "preference": "cheap",
        "vacation_start_month": 5,
        "vacation_end_month": 9
    }'

# Health check
curl https://www.yourdomain.com/api/health
# {"status":"ok"}
```
