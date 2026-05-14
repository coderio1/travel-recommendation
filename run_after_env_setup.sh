#!/bin/bash

# ---------------------------------------------------------------------------
# 1. Run Docker if it's not running.
# ---------------------------------------------------------------------------

if ! docker info > /dev/null 2>&1; then
    echo "Docker daemon is not running. Starting..."
    case "$OS" in
        macos)
            open -a Docker
            ;;
        linux)
            sudo systemctl start docker
            ;;
        wsl)
            DOCKER_EXE="/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe"
            if [ -f "$DOCKER_EXE" ]; then
                "$DOCKER_EXE" &
            else
                echo "ERROR: Docker Desktop not found at the expected path. Start it from Windows manually."
                exit 1
            fi
            ;;
        windows)
            DOCKER_EXE="$PROGRAMFILES/Docker/Docker/Docker Desktop.exe"
            if [ -f "$DOCKER_EXE" ]; then
                start "" "$DOCKER_EXE"
            else
                echo "ERROR: Docker Desktop not found. Start it manually."
                exit 1
            fi
            ;;
    esac

    echo -n "Waiting for Docker to become ready"
    WAIT=0
    until docker info > /dev/null 2>&1; do
        echo -n "."
        sleep 2
        WAIT=$((WAIT + 2))
        if [ "$WAIT" -ge 60 ]; then
            echo ""
            echo "ERROR: Docker did not start within 60 seconds. Please start it manually."
            exit 1
        fi
    done
    echo ""
    echo "Docker is ready."
fi

# ---------------------------------------------------------------------------
# 2. Create external Docker volumes required by docker-compose.yml.
# ---------------------------------------------------------------------------
for volume in travel_db travel_app; do
    if docker volume inspect "$volume" > /dev/null 2>&1; then
        echo "Volume '$volume' already exists, skipping."
    else
        docker volume create "$volume"
        echo "Volume '$volume' created."
    fi
done

# ---------------------------------------------------------------------------
# 3. Read DOMAIN from .env and generate mkcert self-signed certificates.
# ---------------------------------------------------------------------------
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env not found at $ENV_FILE"
    exit 1
fi

DOMAIN=$(grep -E '^DOMAIN=' "$ENV_FILE" | cut -d '=' -f2 | tr -d '[:space:]')

if [ -z "$DOMAIN" ]; then
    echo "ERROR: DOMAIN not set in .env"
    exit 1
fi

echo "Domain: $DOMAIN"

CERT_DIR="$SCRIPT_DIR/traefik/cert"
mkdir -p "$CERT_DIR"

if ! command -v mkcert > /dev/null 2>&1; then
    case "$OS" in
        macos)   MKCERT_HINT="brew install mkcert" ;;
        linux)   MKCERT_HINT="sudo apt install mkcert   # or: sudo snap install mkcert" ;;
        wsl)     MKCERT_HINT="brew install mkcert  (inside WSL)  or  choco install mkcert  (Windows)" ;;
        windows) MKCERT_HINT="choco install mkcert   # or: winget install FiloSottile.mkcert" ;;
    esac
    echo "ERROR: mkcert not found. Install with: $MKCERT_HINT"
    exit 1
fi

mkcert -install 2>/dev/null || true

mkcert \
    -cert-file "$CERT_DIR/cert.pem" \
    -key-file  "$CERT_DIR/key.pem" \
    "$DOMAIN" "www.$DOMAIN" "traefik.$DOMAIN"

echo "Certificates written to $CERT_DIR/"

# ---------------------------------------------------------------------------
# 4. Add DOMAIN and its subdomains to /etc/hosts (idempotent).
# ---------------------------------------------------------------------------
HOSTS_LINE="127.0.0.1 $DOMAIN www.$DOMAIN traefik.$DOMAIN"

case "$OS" in
    wsl)     HOSTS_FILE="/mnt/c/Windows/System32/drivers/etc/hosts" ;;
    windows) HOSTS_FILE="/c/Windows/System32/drivers/etc/hosts" ;;
    *)       HOSTS_FILE="/etc/hosts" ;;
esac

if grep -qF "$DOMAIN" "$HOSTS_FILE" 2>/dev/null; then
    echo "$HOSTS_FILE already contains an entry for $DOMAIN, skipping."
else
    case "$OS" in
        wsl|windows)
            # Requires the shell to be running as Administrator on Windows.
            echo "$HOSTS_LINE" >> "$HOSTS_FILE" 2>/dev/null || {
                echo "ERROR: Cannot write to $HOSTS_FILE."
                echo "       Re-run this script from an Administrator shell."
                exit 1
            }
            ;;
        *)
            echo "$HOSTS_LINE" | sudo tee -a "$HOSTS_FILE" > /dev/null
            ;;
    esac
    echo "Added to $HOSTS_FILE: $HOSTS_LINE"
fi