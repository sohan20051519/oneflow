# OneFlow Environment Architecture & Automated Setup Guide

## Executive Summary

If you run `setup.sh` in a clean directory **without cloning the repository beforehand**, the setup script will:

1. **Auto-Detect Missing Source**: Identify that the OneFlow source tree and configuration templates are not present locally.
2. **Auto-Clone the Repository**: Automatically execute `git clone https://github.com/sohan20051519/oneflow.git source/` to pull the complete codebase.
3. **Provision All Environment Files**: Automatically generate and configure all **7 distinct `.env` files** from their respective `.env.example` templates.
4. **Generate Cryptographic Keys**: Automatically create a 50-character random Django `SECRET_KEY`, a 16-byte hex `MACHINE_SIGNATURE`, and a secure `LIVE_SERVER_SECRET_KEY`.
5. **Propagate Deployment Domain**: Prompt you once for your deployment domain or IP (e.g. `oneflow.cubeone.in` or `13.234.29.32`), then automatically propagate the domain, CORS whitelist, CSRF origins, and Caddy proxy directives across all environment files.
6. **Orchestrate Containers**: Launch the application using Docker Compose with zero manual configuration required.

---

## Environment Files Summary Table

OneFlow utilizes a layered multi-service environment architecture. There are **7 active environment files** created across the deployment:

| # | Environment File Path | Primary Service / Component | Template Source | Purpose |
|---|---|---|---|---|
| **1** | `plane.env` *(symlinked to `.env`)* | **Deploy Root / Docker Compose** | `deployments/aio/community/variables.env` | **Single Source of Truth** for the entire deployment (DB credentials, Redis, domain, AWS S3, Keycloak, SMTP, replicas). |
| **2** | `source/.env` | **Source Root / Compose Override** | `source/.env.example` | Root compose environment when building/running directly inside the `source/` tree. |
| **3** | `source/apps/api/.env` | **Backend REST API & Worker** (`api`, `bgworker`) | `source/apps/api/.env.example` | Django backend settings, database connections, Redis Celery broker, JWT secrets. |
| **4** | `source/apps/web/.env` | **Next.js Main Frontend** (`web`) | `source/apps/web/.env.example` | Web app frontend environment, relative API proxy paths, telemetry flags. |
| **5** | `source/apps/admin/.env` | **God-Mode Dashboard** (`admin`) | `source/apps/admin/.env.example` | Vite/React Admin console environment, relative API routing for `/god-mode/`. |
| **6** | `source/apps/space/.env` | **Spaces Public Portal** (`space`) | `source/apps/space/.env.example` | Next.js public workspace portal for shared docs and issues. |
| **7** | `source/apps/live/.env` | **Live Collab Engine** (`plane-live`) | `source/apps/live/.env.example` | Node.js real-time WebSocket server for issue and document collaboration. |

---

## Detailed Breakdown of Each Environment File

```
plane/
├── plane.env                   <-- [1] DEPLOY ROOT (Single Source of Truth)
├── .env                        <-- Symlink to plane.env
└── source/
    ├── .env                    <-- [2] SOURCE COMPOSE ROOT
    └── apps/
        ├── api/.env            <-- [3] DJANGO API & BACKGROUND WORKER
        ├── web/.env            <-- [4] NEXT.JS WEB APP
        ├── admin/.env          <-- [5] VITE GOD-MODE ADMIN
        ├── space/.env          <-- [6] NEXT.JS PUBLIC SPACES
        └── live/.env           <-- [7] WEBSOCKET COLLABORATION ENGINE
```

---

### 1. Root Deploy Environment: `plane.env` (and `.env`)

**Location**: `/home/ubuntu/plane/plane.env` (symlinked to `/home/ubuntu/plane/.env`)  
**Role**: Passed directly to `docker compose --env-file plane.env up -d`. Controls all container runtime environment variables.

#### Key Variables & Default Values:
```ini
# Canonical Domain (Propagated dynamically by setup.sh)
ONEFLOW_DOMAIN=https://oneflow.cubeone.in
DOMAIN_NAME=oneflow.cubeone.in
WEB_URL=https://oneflow.cubeone.in
SITE_ADDRESS=oneflow.cubeone.in

# Service Replicas
WEB_REPLICAS=1
SPACE_REPLICAS=1
ADMIN_REPLICAS=1
API_REPLICAS=1
WORKER_REPLICAS=1
LIVE_REPLICAS=1

# PostgreSQL Database
POSTGRES_USER=plane
POSTGRES_PASSWORD=plane
POSTGRES_DB=plane
PGDATA=/var/lib/postgresql/data
DATABASE_URL=postgresql://plane:plane@plane-db:5432/plane

# Redis & Celery Task Broker
REDIS_HOST=plane-redis
REDIS_PORT=6379
REDIS_URL=redis://plane-redis:6379/
CELERY_BROKER_URL=redis://plane-redis:6379/1

# Security & Machine Signature
SECRET_KEY=60gp0byfz2dvffa45cxl20p1scy9xbpf6d8c5y0geejgkyp1b5
MACHINE_SIGNATURE=386782294da1c7c9ecda86ee9775bb9b

# CORS & CSRF Security (Allows configured domain + localhost)
CORS_ALLOWED_ORIGINS=https://oneflow.cubeone.in,http://oneflow.cubeone.in
CSRF_TRUSTED_ORIGINS=https://oneflow.cubeone.in,http://oneflow.cubeone.in

# AWS S3 Storage
AWS_REGION=ap-south-1
AWS_STORAGE_BUCKET_NAME=oneflow-staging-uploads
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=LVZ...
USE_MINIO=0
AWS_S3_ENDPOINT_URL=

# Keycloak / OIDC SSO Authentication
KEYCLOAK_CLIENT_ID=OneFlow
KEYCLOAK_CLIENT_SECRET=<encrypted_secret>
KEYCLOAK_ISSUER_URL=https://stgsso.cubeone.in/realms/fstech
KEYCLOAK_REDIRECT_URI=https://oneflow.cubeone.in/auth/oidc/callback/
KEYCLOAK_POST_LOGOUT_REDIRECT_URI=https://oneflow.cubeone.in/

# SMTP Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=notifications@cubeone.in
EMAIL_HOST_PASSWORD=<app_password>
EMAIL_USE_TLS=1
EMAIL_FROM=notifications@cubeone.in
```

---

### 2. Source Compose Root: `source/.env`

**Location**: `source/.env` (generated from `source/.env.example`)  
**Role**: Environment context when running commands inside the `source/` folder.

#### Key Variables:
```ini
APP_DOMAIN=oneflow.cubeone.in
ONEFLOW_DOMAIN=https://oneflow.cubeone.in
SITE_ADDRESS=oneflow.cubeone.in
WEB_URL=https://oneflow.cubeone.in
CORS_ALLOWED_ORIGINS=https://oneflow.cubeone.in,http://oneflow.cubeone.in
DATABASE_URL=postgresql://plane:plane@plane-db:5432/plane
REDIS_URL=redis://plane-redis:6379/
AWS_STORAGE_BUCKET_NAME=oneflow-staging-uploads
```

---

### 3. Backend API & Celery Worker: `source/apps/api/.env`

**Location**: `source/apps/api/.env` (generated from `source/apps/api/.env.example`)  
**Role**: Read directly by Python Django when starting `gunicorn` (`api` container) and `celery` (`bgworker` container).

#### How `setup.sh` Automatically Sanitizes It:
- Rewrites `DATABASE_URL` from local `localhost` to container DNS `postgresql://plane:plane@plane-db:5432/plane`.
- Rewrites `REDIS_URL` to `redis://plane-redis:6379/`.
- Configures `CELERY_BROKER_URL="redis://plane-redis:6379/1"`.
- Sets `GUNICORN_WORKERS="1"` (optimized for 1GB - 4GB RAM instances).
- Generates a fresh 50-character random `SECRET_KEY` if missing or default.
- Clears hardcoded dev ports (`:3000`, `:3001`, `:3002`, `:8000`) so Caddy handles all reverse-proxy routing via clean relative paths.

---

### 4. Web Frontend: `source/apps/web/.env`

**Location**: `source/apps/web/.env` (generated from `source/apps/web/.env.example`)  
**Role**: Next.js production build and runtime environment for the primary web interface.

#### Key Variables:
```ini
NEXT_PUBLIC_API_BASE_URL=""
NEXT_PUBLIC_APP_ENVIRONMENT="production"
NEXT_PUBLIC_DEPLOY_URL="https://oneflow.cubeone.in"
NEXT_PUBLIC_ENABLE_TELEMETRY="0"
```
*Note*: `NEXT_PUBLIC_API_BASE_URL` is deliberately set to empty (`""`) so the browser uses relative API calls (`/api/...`), enabling Caddy to reverse-proxy to the backend without CORS or mixed-content issues.

---

### 5. Admin / God-Mode Dashboard: `source/apps/admin/.env`

**Location**: `source/apps/admin/.env` (generated from `source/apps/admin/.env.example`)  
**Role**: Vite/React environment for the system instance administration panel (`/god-mode/`).

#### Key Variables:
```ini
VITE_APP_API_BASE_URL=""
VITE_APP_DEPLOY_URL="https://oneflow.cubeone.in"
VITE_APP_BASE_PATH="/god-mode"
```

---

### 6. Spaces Public Portal: `source/apps/space/.env`

**Location**: `source/apps/space/.env` (generated from `source/apps/space/.env.example`)  
**Role**: Next.js public documentation and issue sharing portal (`/spaces/`).

#### Key Variables:
```ini
NEXT_PUBLIC_SPACE_BASE_PATH="/spaces"
NEXT_PUBLIC_API_BASE_URL=""
```

---

### 7. Live Collaboration Server: `source/apps/live/.env`

**Location**: `source/apps/live/.env` (generated from `source/apps/live/.env.example`)  
**Role**: Node.js WebSocket engine powering live multi-user cursor tracking, document sync, and real-time updates.

#### How `setup.sh` Automatically Sanitizes It:
- Sets `API_BASE_URL="http://api:8000"` (connects over internal Docker bridge network).
- Sets `REDIS_HOST="plane-redis"` and `REDIS_URL="redis://plane-redis:6379/"`.
- Generates `LIVE_SERVER_SECRET_KEY="secret-key"` to securely authenticate websocket handshakes with Django.

---

## Setup Execution Flow: How `.env` Files Are Generated

```mermaid
flowchart TD
    Start([Run ./setup.sh]) --> CheckSource{Source code present?}
    CheckSource -- No --> GitClone[git clone oneflow repo into source/]
    CheckSource -- Yes --> PromptDomain[Prompt Deployment Domain]
    GitClone --> PromptDomain
    
    PromptDomain --> SyncDomain[Domain & Protocol Normalization]
    SyncDomain --> Step1[Step 1: Copy .env.example -> .env for all 6 apps]
    Step1 --> Step1Sanitize[Sanitize container URLs: plane-db, plane-redis]
    Step1Sanitize --> Step2[Step 2: Generate SECRET_KEY & MACHINE_SIGNATURE]
    Step2 --> Step3[Step 3: Propagate Domain & CORS to all 7 .env files]
    Step3 --> Step4[Step 4: Launch Dual-Pane TUI & Docker Compose]
    Step4 --> Complete([Deployment Live])
```

---

## Running Setup in a Fresh Directory (Without Prior Clone)

You can run `setup.sh` on any fresh Ubuntu/Debian server with a single command:

```bash
mkdir -p /home/ubuntu/plane && cd /home/ubuntu/plane
curl -fsSL https://raw.githubusercontent.com/sohan20051519/oneflow/main/setup.sh -o setup.sh
chmod +x setup.sh
./setup.sh
```

### What Happens Automatically:
1. `setup.sh` detects that `source/` is missing and automatically clones the repo.
2. It prompts:
   ```text
    ╭─[ DEPLOYMENT DOMAIN CONFIGURATION ]────────────────────────╮
    │  Enter the public domain or IP address for OneFlow.        │
    │  Examples: oneflow.cubeone.in or 13.234.29.32              │
    ╰────────────────────────────────────────────────────────────╯

    Enter Domain [default: 13.234.29.32]: 
   ```
3. When you press Enter or provide a domain, it initializes all 7 `.env` files, generates cryptographic keys, sets up container networking, and launches the interactive dual-pane TUI.
