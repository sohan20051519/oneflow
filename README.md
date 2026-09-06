<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="logos/dark.png">
    <source media="(prefers-color-scheme: light)" srcset="logos/light.png">
    <img src="logos/dark.png" alt="one flow" width="340" />
  </picture>
</p>

<p align="center">
  <b>intelligent, streamlined project management & workflow automation</b><br>
  <i>part of the onebiz platform ecosystem</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.1.4-E81B5B?style=flat-square" alt="Version 3.1.4" />
  <img src="https://img.shields.io/badge/license-AGPL--3.0-171717?style=flat-square" alt="License AGPLv3" />
  <img src="https://img.shields.io/badge/brand_kit-onebiz_v2.0-E81B5B?style=flat-square" alt="onebiz Brand Kit" />
  <img src="https://img.shields.io/badge/docker-compose-0db7ed?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/react_router-CA4245?style=flat-square&logo=react-router&logoColor=white" alt="React Router" />
  <img src="https://img.shields.io/badge/django-092E20?style=flat-square&logo=django&logoColor=white" alt="Django" />
</p>

---

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Server Prerequisites](#-server-prerequisites)
- [Production Server Installation](#-production-server-installation)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Environment Configuration](#2-environment-configuration)
  - [3. Keycloak / OneSSO Authentication](#3-keycloak--onesso-authentication)
  - [4. Deploy Containers](#4-deploy-containers)
  - [5. Verify Services & Health Checks](#5-verify-services--health-checks)
- [Local Development Setup](#-local-development-setup)
- [Environment Variables Reference](#-environment-variables-reference)
- [Operational Commands & Maintenance](#-operational-commands--maintenance)
- [Brand Identity & Design System](#-brand-identity--design-system)
- [License](#-license)

---

## 🚀 Overview

**one flow** is a modern, extensible project management and issue-tracking platform built for high-velocity software engineering teams. Designed around speed, clarity, and visual aesthetics, one flow provides powerful planning primitives without unnecessary overhead.

### Why one flow?

- **Zero Clutter**: Clean, purposeful interfaces focused on task execution and milestone delivery.
- **Brand Identity**: Styled natively with the **onebiz design system** (Rose/Coral `#E81B5B` primary accent, dark/light themes).
- **Self-Hosted & Independent**: Full control over your data, database, object storage, and user credentials.
- **Enterprise-Ready SSO**: Out-of-the-box OAuth2 and OIDC integration with Keycloak, Google, GitHub, and custom identity providers.

---

## 🌟 Key Features

| Feature | Description |
| :--- | :--- |
| **Work Items** | Comprehensive task tracking with markdown descriptions, sub-properties, attachments, and custom attributes. |
| **Flexible Layouts** | Instant toggling between **Board** (default), **List**, **Calendar**, and **Spreadsheet** views. |
| **Cycles** | Structured sprints with automated rollover, burn-down velocity graphs, and completion analytics. |
| **Modules** | Subdivide large deliverables into cross-functional milestones with individual ownership and timelines. |
| **Views & Filters** | Global and project-level custom filters. Save, share, and export segmented task queries. |
| **Pages & Docs** | Collaborative rich-text editor with AI-assisted drafting, live components, and embedded tasks. |
| **Analytics Dashboard** | Live progress metrics, workload distribution across team members, and priority heatmaps. |
| **Dual Theme Engine** | High-contrast dark and light modes with persistent user preference storage. |

---

## 🏛️ System Architecture

one flow runs as an orchestrated multi-service architecture via Docker Compose:

```
                          ┌──────────────────────────┐
                          │   Internet / Clients     │
                          └─────────────┬────────────┘
                                        │  Ports 80 / 443
                                        ▼
                          ┌──────────────────────────┐
                          │   Caddy / Reverse Proxy  │
                          └──────┬────────────┬──────┘
                                 │            │
             ┌───────────────────┘            └───────────────────┐
             ▼                                                    ▼
┌──────────────────────────┐                             ┌──────────────────────────┐
│        web               │                             │         api              │
│  React Router + Nginx    │                             │  Django REST Framework   │
│  Port 3000 (Internal)    │                             │  Port 8000 (Internal)    │
└────────────┬─────────────┘                             └────────────┬─────────────┘
             │                                                        │
             │           ┌─────────────────┬──────────────────────────┤
             │           │                 │                          │
             ▼           ▼                 ▼                          ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      ┌──────────────┐
     │  live engine │ │ worker/beat  │ │  PostgreSQL  │      │ Valkey/Redis │
     │  WebSocket   │ │ Celery Task  │ │  Database    │      │ Cache/Queue  │
     └──────────────┘ └──────────────┘ └──────────────┘      └──────────────┘
                                               │                      │
                                               ▼                      ▼
                                        ┌──────────────┐      ┌──────────────┐
                                        │ MinIO S3     │      │ RabbitMQ     │
                                        │ Object Store │      │ Message Bus  │
                                        └──────────────┘      └──────────────┘
```

---

## 💻 Server Prerequisites

Before installing one flow on your production server, verify the following requirements:

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **Operating System** | Ubuntu 22.04 / 24.04 LTS | Ubuntu 24.04 LTS (x86_64 or ARM64) |
| **Processor (CPU)** | 2 vCPU cores | 4+ vCPU cores |
| **Memory (RAM)** | 4 GB RAM | 8+ GB RAM (with 2GB Swap) |
| **Disk Storage** | 25 GB Available SSD | 50+ GB SSD |
| **Network** | Public IP with Ports `80` and `443` open | Static IP + DNS A-Record configured |
| **Software** | Docker Engine 24.0+ & Docker Compose v2 | Docker Engine 26.0+ |

---

## 🛠️ Production Server Installation

### 1. Clone Repository

SSH into your target host and clone the repository:

```bash
cd /home/ubuntu
git clone https://github.com/sohan20051519/oneflow.git oneflow
cd oneflow
```

### 2. Environment Configuration

Generate the core environment configuration file:

```bash
cp plane.env.example plane.env
```

Edit `plane.env` to set your instance parameters:

```bash
nano plane.env
```

Key environment configurations:

```ini
# Domain & Protocol
DOMAIN_NAME=your-domain.com
WEB_URL=https://your-domain.com

# Database (PostgreSQL)
POSTGRES_DB=oneflow
POSTGRES_USER=oneflow
POSTGRES_PASSWORD=generate_a_secure_password_here

# Cache & Message Broker
REDIS_PASSWORD=generate_a_secure_password_here
RABBITMQ_DEFAULT_USER=oneflow
RABBITMQ_DEFAULT_PASS=generate_a_secure_password_here

# Object Storage (MinIO)
AWS_ACCESS_KEY_ID=oneflow-minio-key
AWS_SECRET_ACCESS_KEY=oneflow-minio-secret-key
```

### 3. Keycloak / OneSSO Authentication

one flow includes native support for Keycloak / OneSSO via OAuth2-Proxy. Append your client credentials to `plane.env`:

```ini
# ==========================================
# Keycloak / OneSSO Configuration
# ==========================================
OAUTH2_PROXY_CLIENT_ID=oneflow_client
OAUTH2_PROXY_CLIENT_SECRET=your_client_secret_here
OAUTH2_PROXY_COOKIE_SECRET=your_generated_cookie_secret_32bytes=
OAUTH2_PROXY_OIDC_ISSUER_URL=https://sso.your-domain.com/realms/your-realm
OAUTH2_PROXY_REDIRECT_URL=https://your-domain.com/oauth2/callback
```

> **Tip**: Generate a secure 32-byte cookie secret with:
> ```bash
> python3 -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())'
> ```

### 4. Deploy Containers

Launch the container stack with Docker Compose:

```bash
sudo docker compose up -d --build
```

Docker will pull pre-built dependencies, build the frontend web image, run database migrations, and start all backend services in the background.

### 5. Verify Services & Health Checks

Verify that all services are healthy and active:

```bash
sudo docker compose ps
```

Expected output:
```
NAME           IMAGE                    COMMAND                  SERVICE             STATUS
oneflow-api    makeplane/backend-...    "/docker-entrypoint…"    api                 Up (healthy)
oneflow-db     postgres:15.7-alpine     "docker-entrypoint.s…"   plane-db            Up (healthy)
oneflow-live   makeplane/live-...       "node ./dist/index.js"   live                Up (healthy)
oneflow-redis  valkey/valkey:7.2.11     "valkey-server"          plane-redis         Up (healthy)
oneflow-web    plane-frontend:oneflow   "/docker-entrypoint…"    web                 Up (healthy)
oneflow-proxy  caddy:latest             "caddy run"              proxy               Up (healthy)
```

Test HTTP access:
```bash
curl -I http://localhost
```

---

## 🚀 One-Touch Automated Setup & Startup

one flow features an all-in-one automated deployment script (`setup.sh`) that provisions the environment, generates secrets, launches all Docker containers, and runs automated health checks:

```bash
./setup.sh
```

The script automatically executes the following:
1. **Provisions Environment Files**: Generates all required `.env` and `plane.env` files across services.
2. **Generates Cryptographic Secrets**: Configures high-entropy Django `SECRET_KEY`, machine signatures, and access tokens.
3. **Synchronizes Docker Images**: Automatically detects the Docker runtime and ensures `plane-frontend:oneflow` is available.
4. **Orchestrates Containers**: Launches all 21 microservices via Docker Compose in detached mode.
5. **Performs Health Checks**: Continuously polls services until the database, API, and web gateways respond healthy.
6. **Displays Live Dashboard**: Provides access URLs (`http://localhost`, `http://13.234.29.32`) and service management shortcuts.

---

## 💻 Local Development Workflow

If you are developing components individually on your workstation without Docker Compose:

1. **Run Configuration**:
   ```bash
   ./setup.sh
   ```

2. **Start Backend Dependencies**:
   ```bash
   docker compose -f docker-compose-local.yml up -d
   ```

3. **Start Web Application**:
   ```bash
   pnpm dev
   ```

4. Open your browser at `http://localhost:3000`.

---

## ⚙️ Environment Variables Reference

| Variable | Default / Example | Purpose |
| :--- | :--- | :--- |
| `DOMAIN_NAME` | `localhost` | Primary domain name serving one flow. |
| `WEB_URL` | `http://localhost:3000` | Full base URL used for email links and CORS. |
| `SECRET_KEY` | *(50-char random)* | Cryptographic signing key for Django auth. |
| `POSTGRES_DB` | `oneflow` | PostgreSQL database catalog name. |
| `POSTGRES_USER` | `oneflow` | Database master user. |
| `POSTGRES_PASSWORD` | *(secure password)* | Database master authentication token. |
| `REDIS_HOST` | `plane-redis` | In-memory cache & pub/sub broker hostname. |
| `AWS_S3_ENDPOINT_URL` | `http://plane-minio:9090` | Object storage bucket endpoint. |
| `ENABLE_SIGNUP` | `1` | Allow public user account creation (`1` or `0`). |

---

## 🔧 Operational Commands & Maintenance

### Inspect Logs in Real-Time
```bash
# View aggregated stream
sudo docker compose logs -f

# View specific service (e.g. web or api)
sudo docker compose logs -f web
sudo docker compose logs -f api
```

### Restart Application Stack
```bash
sudo docker compose restart
```

### Rebuild After Code Changes
```bash
# Rebuild web frontend image
sudo docker build -f apps/web/Dockerfile.web -t plane-frontend:oneflow .

# Recreate web container seamlessly
sudo docker compose up -d --no-deps --force-recreate web
```

### Clean Docker Build Cache
If server storage drops below 2 GB:
```bash
sudo docker builder prune -a -f
```

---

## 🎨 Brand Identity & Design System

one flow adheres strictly to the **onebiz design system (v2.0)**:

- **Naming**: Always lowercase in prose (**one flow**, **onebiz**). Technical identifier: `oneflow`.
- **Primary Brand Color**: `hsl(352, 82%, 52%)` / `#E81B5B` (Rose / Coral).
- **Typography**: Inter (UI font) · JetBrains Mono (Code & Technical).
- **Corner Radius**: Buttons `8px` (`rounded-lg`) · Cards `12px` (`rounded-xl`) · Inputs `6px` (`rounded-md`).
- **Dark Mode**: Native `class="dark"` with rich neutral surfaces (`#171717`, `#1C1C1C`).

---

## 📄 License

This software is distributed under the **GNU Affero General Public License v3.0** (AGPL-3.0). See [LICENSE.txt](./LICENSE.txt) for full terms.

*Maintained by Sohan A · © 2026 one flow · Part of the onebiz Platform.*
