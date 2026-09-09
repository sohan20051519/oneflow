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
  <img src="https://img.shields.io/badge/next.js-000000?style=flat-square&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/django-092E20?style=flat-square&logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/storage-AWS_S3-FF9900?style=flat-square&logo=amazon-s3&logoColor=white" alt="AWS S3" />
</p>

---

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Container Architecture & Service Explanations](#-container-architecture--service-explanations)
- [Why `oneflow-migrator` Exits with Code 0 (`Exited (0)`)](#-why-oneflow-migrator-exits-with-code-0-exited-0)
- [Storage Architecture: Local Server Data vs. AWS S3](#-storage-architecture-local-server-data-vs-aws-s3)
- [Network Ports & AWS Security Groups Architecture](#-network-ports--aws-security-groups-architecture)
- [Multi-Environment Deployment Guide](#-multi-environment-deployment-guide)
  - [1. Local Development](#1-local-development-setup)
  - [2. Staging Environment](#2-staging-deployment-current-live-setup)
  - [3. Production Deployment](#3-production-deployment-best-practices)
- [Server Prerequisites](#-server-prerequisites)
- [Automated Setup Script (`setup.sh`)](#-automated-setup-script-setupsh)
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
- **Direct AWS S3 Storage**: Fully integrated with AWS S3 for ultra-reliable, high-throughput attachment and media persistence with presigned secure access.
- **Enterprise-Ready SSO**: Out-of-the-box OpenID Connect (OIDC) integration with Keycloak (FS Tech Realm), Google, GitHub, and custom identity providers.
- **Multi-App Architecture**: Dedicated microservices for main task management (`web`), public document sharing (`space`), instance administration (`admin`), and live collaboration (`live`).

---

## 🌟 Key Features

| Feature | Description |
| :--- | :--- |
| **Work Items & Issues** | Comprehensive task tracking with markdown descriptions, sub-properties, custom states, priorities, and attachments. |
| **Flexible Layouts** | Instant toggling between **Board** (Kanban default), **List**, **Calendar**, and **Spreadsheet** views. |
| **Cycles (Sprints)** | Structured sprint management with automated rollover, burndown velocity analytics, and target dates. |
| **Modules (Milestones)** | Subdivide large deliverables into cross-functional epics/milestones with individual ownership and timelines. |
| **Views & Filters** | Global and project-level custom filters. Save, share, and export segmented task queries. |
| **Pages & Docs** | Collaborative rich-text documentation with real-time multi-user editing and embedded live issue widgets. |
| **Public Spaces** | Publish specific project boards, roadmaps, and documentation portals publicly at `/spaces/` for stakeholders. |
| **God-Mode Admin** | Centralized instance administration console at `/god-mode/` for managing workspaces, users, feature flags, and integrations. |
| **Real-time Live Sync** | WebSocket-powered live updates, presence detection, and multi-cursor collaboration. |

---

## 🏛️ System Architecture

one flow operates as a modular, containerized multi-service architecture orchestrated via Docker Compose:

```
                           ┌──────────────────────────┐
                           │   Internet / Clients     │
                           └─────────────┬────────────┘
                                         │  Ports 80 / 443 (HTTPS)
                                         ▼
                           ┌──────────────────────────┐
                           │   proxy (Caddy Gateway)  │
                           └──────┬──────┬──────┬─────┘
                                  │      │      │
       ┌──────────────────────────┼──────┼──────┴──────────────────────────┐
       │ /                        │ /god-mode/  │ /spaces/                 │ /api/*, /auth/*
       ▼                          ▼             ▼                          ▼
┌──────────────┐          ┌──────────────┐ ┌──────────────┐        ┌──────────────┐
│  web (3000)  │          │ admin (3000) │ │ space (3000) │        │  api (8000)  │
│ Next.js App  │          │ Vite / React │ │ Public Portal│        │ Django REST  │
└──────────────┘          └──────────────┘ └──────────────┘        └──────┬───────┘
                                                                          │
                                  ┌───────────────────────────────────────┤
                                  │                                       │
                                  ▼                                       ▼
                         ┌─────────────────┐                     ┌─────────────────┐
                         │ bgworker (8000) │                     │ plane-live(3000)│
                         │ Celery Workers  │                     │ Node WebSockets │
                         └────────┬────────┘                     └────────┬────────┘
                                  │                                       │
                   ┌──────────────┴──────────────┬────────────────────────┘
                   │                             │
                   ▼                             ▼
       ┌───────────────────────┐     ┌───────────────────────┐
       │ plane-db (Port 5432)  │     │ plane-redis(Port 6379)│
       │ PostgreSQL 15 Engine  │     │ Valkey 7.2 (Cache/MQ) │
       └───────────────────────┘     └───────────────────────┘
                   ▲
                   │ Runs DDL schema migrations on startup
       ┌───────────┴───────────┐
       │ plane-migrator        │
       │ One-off Init (Exit 0) │
       └───────────────────────┘
                   │
                   ▼ (User uploads & attachments)
       ┌─────────────────────────────────────────────────────┐
       │               AWS S3 Bucket (Direct)                │
       │  oneflow-staging-uploads / production-uploads       │
       │                 Region: ap-south-1                  │
       └─────────────────────────────────────────────────────┘
```

---

## 📦 Container Architecture & Service Explanations

The stack consists of **10 specialized microservice containers**. Each container fulfills a distinct, isolated responsibility:

### 1. `proxy` (`plane-proxy:latest` / Caddy)
- **Role**: Edge reverse proxy, SSL/TLS termination, and API gateway.
- **Ports Exposed**: `80` (HTTP) and `443` (HTTPS).
- **Internal Routing Logic**:
  - `/` & `/*` $\rightarrow$ `web:3000` (Main Next.js frontend)
  - `/god-mode/*` $\rightarrow$ `admin:3000` (System administration portal)
  - `/spaces/*` $\rightarrow$ `space:3000` (Public documentation/issue portal)
  - `/api/*`, `/auth/*`, `/static/*` $\rightarrow$ `api:8000` (Django REST API)
  - `/live/*` $\rightarrow$ `plane-live:3000` (WebSocket collaboration engine)
- **Features**: Automatic Let's Encrypt SSL certificate provisioning and renewal, gzip/zstd compression, client request buffering, and path routing without CORS friction.

### 2. `web` (`plane-web:latest`)
- **Role**: Primary client-facing web application.
- **Technology**: React, Next.js, TailwindCSS, onebiz Design System v2.0.
- **Port**: `3000` (Internal).
- **Function**: Renders all primary workspaces, Kanban boards, issue lists, cycle roadmaps, module timelines, and rich-text document editors.

### 3. `admin` (`plane-admin:latest`)
- **Role**: God-Mode instance administration console.
- **Technology**: React, Vite, TailwindCSS.
- **Path**: Accessible at `https://<domain>/god-mode/`.
- **Port**: `3000` (Internal).
- **Function**: Allows instance administrators to manage organizations, global users, feature flag toggles, authentication providers, and system telemetry.

### 4. `space` (`plane-space:latest`)
- **Role**: Public portal for external sharing.
- **Technology**: Next.js, React.
- **Path**: Accessible at `https://<domain>/spaces/`.
- **Port**: `3000` (Internal).
- **Function**: Generates read-only and interactive public views of specific boards, project backlogs, and pages shared with external clients or open-source communities.

### 5. `plane-live` (`plane-live:latest`)
- **Role**: Real-time multiplayer synchronization engine.
- **Technology**: Node.js, WebSockets (`ws`), Valkey Pub/Sub.
- **Port**: `3000` (Internal).
- **Function**: Facilitates collaborative real-time typing in docs, instant issue status updates across multiple browser tabs, user presence indicators, and live cursor tracking.

### 6. `api` (`oneflow-api:latest`)
- **Role**: Core application backend and REST API engine.
- **Technology**: Python 3.11, Django REST Framework, Gunicorn WSGI.
- **Port**: `8000` (Internal).
- **Function**: Executes all core business logic, database queries, authentication verification (JWT & Keycloak OIDC sessions), workspace permissions, and presigned AWS S3 upload/download URL generation.
- **Startup Dependency**: Strictly waits for `plane-db` (healthy), `plane-redis` (healthy), and `migrator` (`service_completed_successfully`).

### 7. `bgworker` (`oneflow-worker:latest`)
- **Role**: Asynchronous background job worker.
- **Technology**: Python, Celery, Valkey/Redis task queue broker.
- **Port**: `8000` (Internal, non-exposed).
- **Function**: Processes background tasks out of the critical HTTP request path: sending transactional emails, webhook delivery, CSV/JSON exports and imports, periodic cycle rollover calculations, and third-party integrations (Slack, GitHub).

### 8. `plane-migrator` (`oneflow-migrator:latest`)
- **Role**: Database schema migrator and initial seed runner.
- **Technology**: Python, Django management command (`python manage.py migrate`).
- **Lifecycle**: **Run-to-completion (Ephemeral)**. Exits cleanly with code 0 once all migrations finish. *(See detailed explanation below).*

### 9. `plane-db` (`postgres:15.7-alpine`)
- **Role**: Master relational transactional database.
- **Technology**: PostgreSQL 15 Alpine.
- **Port**: `5432` (Internal).
- **Storage**: Persistent bind mount at `/home/ubuntu/plane/data/db`.
- **Function**: Persists all relational entities: users, workspace memberships, issue metadata, activity logs, cycles, and comments.

### 10. `plane-redis` (`valkey/valkey:7.2.11-alpine`)
- **Role**: In-memory cache, session store, and Celery broker.
- **Technology**: Valkey 7.2 (high-performance open-source fork of Redis).
- **Port**: `6379` (Internal).
- **Storage**: Persistent bind mount at `/home/ubuntu/plane/data/redis`.
- **Function**: Database 0 handles transient application caching and WebSocket pub/sub; Database 1 handles the Celery asynchronous task distribution queue.

---

## 🔍 Why `oneflow-migrator` Exits with Code 0 (`Exited (0)`)

When inspecting containers with `docker ps -a`, you will observe:
```text
CONTAINER ID   IMAGE                     COMMAND                  STATUS
806dda5a11ba   oneflow-migrator:latest   "./bin/docker-entryp…"   Exited (0) 17 minutes ago   plane-migrator
```

### Explanation:
1. **It is an Init Job, NOT a Daemon**: Unlike a web server (`web`) or API server (`api`) that must stay continuously alive to listen for incoming network sockets, `plane-migrator` is a **one-time initialization task** (an "init container" or "batch job").
2. **What it Executes**:
   The container runs `./bin/docker-entrypoint-migrator.sh`:
   ```bash
   #!/bin/bash
   set -e
   python manage.py wait_for_db
   echo "Applying database migrations..."
   until python manage.py migrate; do
       echo "Retrying..."
       sleep 3
   done
   echo "Database migrations applied successfully."
   ```
   This script waits for PostgreSQL to become ready, applies any pending Django database schema migrations (`CREATE TABLE`, `ALTER TABLE`, new columns, indexes), seeds initial data, and finishes.
3. **What `Exit (0)` Signifies**: In POSIX and Linux standards, an exit code of `0` denotes **complete and unmitigated success** (any non-zero code such as `1` or `137` denotes an error or kill signal).
4. **Orchestration Workflow**:
   In `docker-compose.yml`:
   ```yaml
   migrator:
     image: oneflow-migrator:latest
     container_name: plane-migrator
     restart: "no"                  # Do NOT restart after finishing
   
   api:
     depends_on:
       migrator:
         condition: service_completed_successfully # API waits for migrator exit 0
   ```
   Docker Compose starts `plane-migrator`, waits for it to finish applying all database tables, confirms that it exited with code 0, and only then starts the `api` and `bgworker` services. **Seeing `Exited (0)` indicates your database is completely healthy and up to date.**

---

## 💾 Storage Architecture: Local Server Data vs. AWS S3

one flow implements a clean hybrid storage architecture: all transactional, relational, and real-time state is stored **locally on the server** (PostgreSQL, Valkey/Redis, and host directories), while all binary file assets, attachments, and media blobs are stored **in AWS S3**.

```
┌────────────────────────────────────────────────────────┐
│                   one flow Platform                    │
└───────────────────────────┬────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│     Local Server      │       │        AWS S3         │
│  (EC2 / Host Storage) │       │   (Cloud Object Store)│
├───────────────────────┤       ├───────────────────────┤
│ • PostgreSQL Database │       │ • Issue Attachments   │
│ • Valkey/Redis State  │       │ • Editor Embeds/Media │
│ • Document Binary CRDT│       │ • User Avatars        │
│ • File Metadata & URLs│       │ • Project Cover Art   │
│ • Caddy SSL Certs     │       │ • Workspace Logos     │
│ • Docker Logs/Configs │       │ • Data Exports (CSV)  │
└───────────────────────┘       └───────────────────────┘
```

### 1. What is Stored in AWS S3 (`AWS_STORAGE_BUCKET_NAME`)

AWS S3 acts as the primary object storage backend. Only binary file bytes and media assets are stored in the bucket:

* **Issue & Task Attachments:**
  * Files attached directly to issues (PDFs, ZIPs, spreadsheets, logs, videos, audio, etc.).
  * Screenshots, diagrams, and inline images pasted into issue descriptions or comments.
* **Document & Page Editor Media:**
  * Images and attachments embedded inside collaborative rich-text Pages and document blocks.
* **User & Workspace Branding Assets:**
  * User profile photos and avatars.
  * Workspace logos and custom brand icons.
  * Project cover images (uploaded by users) and custom project icons.
* **Export Artifacts:**
  * Workspace and project exports (CSV, JSON, XLSX) generated asynchronously by background Celery worker tasks. Download links are securely issued via presigned S3 URLs with automatic time-based expiration.
* **Import Staging Files:**
  * Uploaded migration files (from Jira, GitHub, or CSV) while being processed by the background worker.

> **Architecture Note:** The database **never** stores raw file binaries. PostgreSQL only stores the **metadata record** (`FileAsset` model: file name, file size in bytes, MIME type, uploader user ID, and S3 asset key/URL).

---

### 2. What is Stored Locally on the Server

All operational, relational, and real-time data is persisted locally on the host machine:

#### A. PostgreSQL Database (`/home/ubuntu/plane/data/db`)
Mounted directly to the `plane-db` container. Persists all core business logic and structured records:
* **Users & Workspaces:** User accounts, hashed credentials, Keycloak/OIDC IDs, workspace memberships, role-based access control (RBAC), and user profile settings.
* **Work Items & Issues:** Issue titles, markdown/HTML descriptions, priority, status/state (*Backlog, Todo, In Progress, Done, Cancelled*), assignees, labels, estimates, deadlines, and parent-child hierarchies.
* **Cycles & Modules:** Sprint configurations, start/end dates, burndown metrics, milestone ownership, and progress tracking.
* **Comments & Activities:** All issue comments, threaded replies, emoji reactions, and the complete audit trail / activity history.
* **Pages & Document Contents:** Document text (`description_html`) and real-time collaborative state (`description_binary` Yjs CRDT data synced by the `live` service).
* **Asset Metadata Pointers:** Table of `FileAsset` records referencing the external S3 object paths.

#### B. Valkey / Redis (`/home/ubuntu/plane/data/redis`)
Mounted to the `plane-redis` container for fast in-memory caching and messaging:
* **Background Task Queues (Database 1):** Celery job broker for sending emails, firing webhook events, executing background exports/imports, and calculating rollover cycles.
* **Real-time Live Collaboration (Database 0):** WebSocket pub/sub channels (`hocuspocus:admin`), active document subscriber channels, user presence, and multi-user cursor awareness states.
* **Application Cache:** Ephemeral API response caches, session states, and rate-limiting counters.

#### C. Local Host Filesystem (`/home/ubuntu/`)
* **Codebase & Configs:** Git repository (`~/oneflow`), Docker Compose files, and environment files (`.env`, `apps/api/.env`, `apps/web/.env`, etc.).
* **Reverse Proxy & SSL:** Caddy reverse-proxy configuration and automated Let's Encrypt TLS certificates.
* **Container Storage & Logs:** Docker container layers, volume metadata, and system logs (`/var/lib/docker/containers/`).

---

### 3. Storage Comparison Matrix

| Data Category | Stored Locally (PostgreSQL / Redis / Host) | Stored in AWS S3 | Description |
| :--- | :---: | :---: | :--- |
| **User Accounts & Roles** | ✅ **Local (PostgreSQL)** | ❌ | User profiles, emails, role assignments, workspace settings. |
| **Issues, Cycles & Modules** | ✅ **Local (PostgreSQL)** | ❌ | Titles, descriptions, states, assignees, dates, sprint metrics. |
| **Comments & Activity Logs** | ✅ **Local (PostgreSQL)** | ❌ | Full issue audit history, comments, and reactions. |
| **Page / Document Text** | ✅ **Local (PostgreSQL)** | ❌ | Rich-text content (HTML) and Yjs CRDT binary document states. |
| **File Attachments (PDFs, ZIPs)** | Metadata only | ✅ **AWS S3** | Raw file bytes stored in S3; database stores name, size, S3 URL. |
| **Pasted Images & Screenshots** | Metadata only | ✅ **AWS S3** | Image blobs stored in S3; markdown links reference S3 keys. |
| **User Avatars & Project Covers**| URL reference only | ✅ **AWS S3** | Uploaded profile pictures, project cover images, workspace logos. |
| **Export Files (CSV, JSON, XLSX)**| Job record only | ✅ **AWS S3** | Generated reports stored temporarily with presigned S3 URLs. |
| **Live Multi-Cursor & Presence** | ✅ **Local (Redis)** | ❌ | Ephemeral real-time collaborative state and awareness. |
| **Async Background Queues** | ✅ **Local (Redis)** | ❌ | Celery queue for emails, notifications, and scheduled tasks. |
| **SSL / TLS Certificates** | ✅ **Local (Host / Caddy)** | ❌ | Auto-managed Let's Encrypt certificates on server. |

---

### 4. Backup & Maintenance Recommendations

1. **Local Data Backup (Server):**
   * Regularly backup the PostgreSQL directory `/home/ubuntu/plane/data/db` using standard `pg_dump`:
     ```bash
     sudo docker exec -t plane-db pg_dump -U plane plane > backup_$(date +%Y%m%d).sql
     ```
2. **S3 Bucket Backup (AWS):**
   * Enable **S3 Versioning** and **Lifecycle Rules** on the S3 bucket (`oneflow-staging-uploads`) in the AWS Console to protect against accidental file deletions and manage storage tiering (e.g. Standard to Glacier/Infrequent Access for old exports).

---

## 🌐 Network Ports & AWS Security Groups Architecture

one flow separates its network architecture into **Public Gateway Ports** (managed via the Caddy reverse proxy) and **Internal Service Ports** (isolated inside Docker's internal virtual bridge network).

```
 ┌─────────────────────────────────────────────────────────────┐
 │                  Internet / Public Traffic                  │
 └──────────────────────┬──────────────────────┬───────────────┘
                        │ Port 80 (HTTP)       │ Port 443 (HTTPS)
                        ▼                      ▼
 ┌─────────────────────────────────────────────────────────────┐
 │           Host Gateway / Reverse Proxy (proxy: Caddy)       │
 └──────────────────────┬──────────────────────────────────────┘
                        │ Isolated Internal Docker Bridge Network
        ┌───────────────┼───────────────┬───────────────┐
        │ Port 3000     │ Port 3000     │ Port 8000     │ Port 5432 / 6379
        ▼               ▼               ▼               ▼
 ┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
 │  web / space ││ live (WS)    ││ api / worker ││  db / redis  │
 │  (Frontend)  ││ (Sync)       ││ (Backend)    ││  (Data Layer)│
 └──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

### 1. Service Port Mappings

| Service | Container Name | Internal Port | Host Port Exposed | Purpose / Protocol |
| :--- | :--- | :---: | :---: | :--- |
| **Reverse Proxy** | `proxy` | `80`, `443` | **`80`, `443`** | **Public Gateway**: Caddy reverse proxy handling HTTP/HTTPS traffic, TLS certificate management, and upstream path routing. |
| **Web App** | `web` | `3000` | None (Internal) | Next.js main user interface. |
| **Admin Console** | `admin` | `3000` | None (Internal) | Instance administration dashboard (`/god-mode/`). |
| **Public Spaces** | `space` | `3000` | None (Internal) | Public document and issue portal (`/spaces/`). |
| **Live Collaboration** | `plane-live` | `3000` | None (Internal) | HocusPocus / Express WebSocket synchronization engine for collaborative editing. |
| **Backend API** | `api` | `8000` | None (Internal) | Django REST Framework API server. |
| **Background Worker** | `bgworker` | — | None (Internal) | Celery asynchronous worker (communicates via Redis, does not listen on a port). |
| **Database** | `plane-db` | `5432` | None (Internal) | PostgreSQL relational database. |
| **Cache & Broker** | `plane-redis` | `6379` | None (Internal) | Valkey / Redis in-memory cache and pub/sub message broker. |

---

### 2. Recommended AWS EC2 Security Group Configuration

Configure your AWS Security Groups following the principle of least privilege:

#### Inbound Rules (Ingress)
Only open the public web ports and restricted administrative SSH:

| Type | Protocol | Port Range | Source | Purpose / Justification |
| :--- | :---: | :---: | :--- | :--- |
| **HTTPS** | TCP | `443` | `0.0.0.0/0` (IPv4)<br>`::/0` (IPv6) | **Required**: Public SSL/TLS entrypoint for all web traffic, API calls, and collaborative WebSockets. |
| **HTTP** | TCP | `80` | `0.0.0.0/0` (IPv4)<br>`::/0` (IPv6) | **Required**: Automated Let's Encrypt ACME HTTP-01 challenge validation and automatic HTTP-to-HTTPS redirection. |
| **SSH** | TCP | `22` | `Your-Admin-IP/32` or Bastion SG | **Administrative**: Server maintenance and terminal access. **Never leave open to `0.0.0.0/0`.** |

> [!CAUTION]
> **Do NOT expose internal ports in your AWS Inbound Security Group:**
> Ports `3000`, `5432`, `6379`, and `8000` are bound exclusively inside Docker's internal virtual bridge network. They must **never** be added to your EC2 Inbound Security Group rules. All client traffic must enter exclusively via Caddy on port `443`.

#### Outbound Rules (Egress)
The EC2 server requires outbound connectivity to communicate with external cloud services:

| Type | Protocol | Port Range | Destination | Purpose / Justification |
| :--- | :---: | :---: | :--- | :--- |
| **HTTPS** | TCP | `443` | `0.0.0.0/0` | Outbound communication to **AWS S3** (`s3.<region>.amazonaws.com`), **Infisical Secret Manager**, **Keycloak / OIDC Identity Providers**, and **Let's Encrypt CA validation**. |
| **HTTP** | TCP | `80` | `0.0.0.0/0` | Operating system package management (`apt-get`) and outgoing webhooks. |
| **Custom TCP / SMTPS** | TCP | `587` or `465` | Mail Host / `0.0.0.0/0` | Outbound transactional email delivery via SMTP (if email notifications are configured). |
| **DNS** | UDP/TCP | `53` | `0.0.0.0/0` (or VPC DNS) | Domain name resolution. |
| *(Default AWS SG)* | **All Traffic** | **All** | `0.0.0.0/0` | Standard AWS outbound default rule allowing all outbound connections is safe and supported. |

---

## 🌍 Unified Multi-Environment Deployment Guide (`setup.sh`)

Both **Staging** and **Production** deployments use `./setup.sh` as the single unified entry point. When executed, the script prompts for:
1. **Domain Configuration**: The canonical deployment domain (e.g. `oneflow.cubeone.in` or production domain).
2. **Environment & Secrets Source**: Provides **3 Options** to supply secrets:
   - **[1] Local `.env` file**: Uses existing local `plane.env` / `.env` on the server.
   - **[2] Self-Hosted Infisical — Production**: Dynamically pulls secrets from self-hosted Infisical (`https://config.cubeone.in`) for the `production` (`prod`) environment [Recommended].
   - **[3] Self-Hosted Infisical — Staging**: Dynamically pulls secrets from self-hosted Infisical (`https://config.cubeone.in`) for the `staging` environment.

```
┌───────────────────────────┬───────────────────────────────────────────────────────────────────┐
│     1. Local Dev          │               2. Staging & Production (via setup.sh)              │
├───────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ • Hot-reload Next.js web  │ • Single command: ./setup.sh                                      │
│ • Local Django API server │ • Prompt 1: Deployment Domain (SSL / Caddy)                       │
│ • Docker backing infra    │ • Prompt 2: Secret Source (Local .env vs Infisical Prod/Staging)  │
│ • http://localhost:3000   │ • Auto-provisions Let's Encrypt HTTPS certificates                │
│                           │ • Polls database migrations & health readiness                    │
└───────────────────────────┴───────────────────────────────────────────────────────────────────┘
```

---

### 1. Local Development Setup (Workstation)

For engineers developing and debugging frontend components or backend APIs locally:

#### Step 1: Start Infrastructure Containers
Run minimal backing services (PostgreSQL, Valkey/Redis) using `docker-compose-local.yml`:
```bash
cd /home/ubuntu/plane/source
docker compose -f docker-compose-local.yml up -d plane-db plane-redis
```

#### Step 2: Run Backend API
Create a Python virtual environment and run the dev server:
```bash
cd /home/ubuntu/plane/source/apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

#### Step 3: Run Frontend Web Application
Install Node dependencies and start the Next.js dev server:
```bash
cd /home/ubuntu/plane/source
pnpm install
pnpm --filter @plane/web dev
```
Access at `http://localhost:3000`. Changes to TypeScript and Python files will hot-reload immediately.

---

### 2. Staging & Production Server Deployments

To launch or update **Staging** or **Production**, run `./setup.sh`:

```bash
cd /home/ubuntu/plane
./setup.sh
```

#### Interactive Flow:

1. **Deployment Domain**:
   ```text
    ╭─[ DEPLOYMENT DOMAIN CONFIGURATION ]────────────────────────╮
    │  Enter the public domain or IP address for OneFlow.        │
    │  Examples: oneflow.cubeone.in or 13.234.29.32              │
    ╰────────────────────────────────────────────────────────────╯

    Enter Domain [default: oneflow.cubeone.in]: 
   ```

2. **Environment & Secrets Source (3 Options)**:
   ```text
    ╭─[ ENVIRONMENT & SECRETS CONFIGURATION ]────────────────────╮
    │  Select how you want to provide environment variables:     │
    │                                                            │
    │    [1] Local .env file (Use local plane.env / .env)        │
    │    [2] Self-Hosted Infisical — Production (config.cubeone) │
    │    [3] Self-Hosted Infisical — Staging (config.cubeone.in) │
    ╰────────────────────────────────────────────────────────────╯

    Select Option [1/2/3, default: 1]: 
   ```

#### How Each Option Works:
- **Option 1 (Local `.env` file)**: Reads the local `plane.env` file on disk. Ideal for deployments with pre-provisioned environment files.
- **Option 2 (Self-Hosted Infisical — Production)** [Recommended]:
  - Connects to self-hosted Infisical cluster at `https://config.cubeone.in`.
  - Project ID: `f10e0d79-aa86-4c35-862a-e44ed0f482e3` (project: `oneflow`).
  - Target Environment: `prod` / `production`.
  - Authenticates via **Universal Auth** (Machine Identity Client ID + Client Secret) or **Service Token** (`st.xxx`).
  - Pulls all production secrets and merges them into `plane.env`.
- **Option 3 (Self-Hosted Infisical — Staging)**:
  - Connects to `https://config.cubeone.in`.
  - Project ID: `f10e0d79-aa86-4c35-862a-e44ed0f482e3`.
  - Target Environment: `staging`.
  - Pulls staging secrets and writes them to `plane.env`.

#### Non-Interactive / CI/CD Automation Flags:
You can pass arguments directly to `./setup.sh` to run unattended:
```bash
# Deploy using local .env
./setup.sh --domain oneflow.cubeone.in --env-source 1 --no-prompt

# Deploy Production pulling from Infisical with Universal Auth
./setup.sh --domain oneflow.cubeone.in --env-source 2 \
  --infisical-client-id "<CLIENT_ID>" --infisical-client-secret "<CLIENT_SECRET>" --no-prompt

# Deploy Staging pulling from Infisical with Service Token
./setup.sh --domain oneflow.cubeone.in --env-source 3 \
  --infisical-token "st.xxxx" --no-prompt
```

---

### 3. God-Mode Administration & Instance Configuration (`/god-mode/`)

OneFlow provides a dedicated system administration console known as **God-Mode** (`/god-mode/`).

#### Available God-Mode Modules:
1. **General** (`/god-mode/general/`): Instance identification, admin user management, telemetry controls.
2. **Configurations** (`/god-mode/configuration/`):
   - **Self-Hosted Infisical Integration**: Direct configuration of Infisical cluster endpoint (`https://config.cubeone.in`), project UUID, environment (`prod`), and Machine Identity credentials.
   - **Live Connection Testing**: Instant health verification and token validation against the Infisical cluster.
   - **Platform Infrastructure Readout**: Live status of Direct AWS S3 storage (`oneflow-storage`), Keycloak OIDC SSO, PostgreSQL transactional database, and Valkey/Redis cache.
3. **Email** (`/god-mode/email/`): SMTP settings, TLS/SSL configuration, and outbound email test tools.
4. **Workspaces** (`/god-mode/workspace/`): Workspace creation controls, workspace listing, and global member quotas.
5. **Authentication** (`/god-mode/authentication/`): Enterprise Keycloak / OpenID Connect SSO, GitHub, GitLab, Google, and Gitea auth toggles.
6. **AI** (`/god-mode/ai/`): LLM model configuration (`gpt-4o-mini`, custom models) and OpenAI credentials.

---

### 4. Production Hardening & Best Practices

When operating OneFlow in Production:
1. **Automate Daily Database Backups**:
   ```bash
   0 2 * * * sudo docker exec plane-db pg_dump -U plane -d plane | gzip > /home/ubuntu/backups/plane_db_$(date +\%F).sql.gz
   ```
2. **S3 Bucket Security**:
   - Production bucket: `oneflow-production-uploads` in `ap-south-1`.
   - Maintain "Block all public access" (all access is securely mediated via presigned URLs).
   - Enable bucket versioning and lifecycle policies to Amazon S3 Glacier.
3. **Scaling**:
   - `GUNICORN_WORKERS=4`
   - `API_REPLICAS=2`
   - `WORKER_REPLICAS=2`

---

## ⚙️ Environment Variables Reference

All environment variables should be defined in your `.env` / `plane.env` file or provisioned securely via Infisical.

| Variable | Format / Example | Description |
| :--- | :--- | :--- |
| `ONEFLOW_DOMAIN` | `https://<your-domain.com>` | Canonical deployment URL (Single source of truth). |
| `DOMAIN_NAME` | `<your-domain.com>` | Domain hostname used for proxy routing and CORS. |
| `POSTGRES_DB` | `plane` | PostgreSQL master database name. |
| `POSTGRES_USER` | `plane` | PostgreSQL master user. |
| `POSTGRES_PASSWORD` | `<secure-database-password>` | PostgreSQL master password. |
| `DATABASE_URL` | `postgresql://<user>:<password>@plane-db:5432/<db_name>` | Full database connection URI. |
| `REDIS_URL` | `redis://plane-redis:6379/` | Cache and pub/sub connection URI. |
| `CELERY_BROKER_URL` | `redis://plane-redis:6379/1` | Celery asynchronous task distribution queue. |
| `AWS_REGION` | `ap-south-1` | AWS region hosting your S3 bucket. |
| `AWS_STORAGE_BUCKET_NAME`| `<your-s3-bucket-name>` | S3 bucket storing user uploads and attachments. |
| `AWS_ACCESS_KEY_ID` | `<your-aws-access-key-id>` | AWS IAM programmatic access key ID. |
| `AWS_SECRET_ACCESS_KEY` | `<your-aws-secret-access-key>` | AWS IAM programmatic secret access key. |
| `USE_MINIO` | `0` | `0` for Direct AWS S3; `1` for self-hosted MinIO. |
| `KEYCLOAK_CLIENT_ID`| `<oidc-client-id>` | Keycloak OpenID Connect Client ID. |
| `KEYCLOAK_CLIENT_SECRET`| `<oidc-client-secret>` | Keycloak OpenID Connect Client Secret. |
| `KEYCLOAK_ISSUER_URL`| `https://<sso-domain>/realms/<realm-name>` | Keycloak OIDC realm endpoint. |
| `LIVE_SERVER_SECRET_KEY`| `<random-secret-token>` | WebSocket authentication handshake secret. |
| `INFISICAL_HOST` | `https://<infisical-domain>` | Self-hosted or Cloud Infisical instance endpoint. |
| `INFISICAL_PROJECT_ID` | `<project-uuid>` | Infisical project UUID. |
| `INFISICAL_ENV` | `prod` / `staging` | Target Infisical secret environment. |
| `INFISICAL_CLIENT_ID` | `<machine-identity-client-id>` | Machine Identity Client ID for Universal Auth. |
| `INFISICAL_CLIENT_SECRET`| `<machine-identity-client-secret>` | Machine Identity Client Secret for Universal Auth. |

---

## 🔧 Operational Commands & Maintenance

### Real-Time Aggregated Logs
```bash
# Aggregated log stream for all services
sudo docker compose logs -f

# Tail specific container logs
sudo docker logs -f api
sudo docker logs -f bgworker
sudo docker logs -f web
sudo docker logs -f proxy
sudo docker logs -f plane-live
```

### Restart Application Stack
```bash
# Restart entire stack
sudo docker compose restart

# Restart specific service (e.g. web, api, or live)
sudo docker compose restart web
```

### Stop & Start Stack
```bash
# Stop all containers cleanly
sudo docker compose down

# Start all containers in background
sudo docker compose up -d
```

### Rebuild and Force-Recreate After Code Updates
```bash
# Pull latest changes from git
git pull origin main

# Rebuild web container and recreate services cleanly
sudo docker compose build web
sudo docker compose up -d --force-recreate --no-deps web
```

### Inspect Container Health & Status
```bash
sudo docker ps -a
```

---

## 🎨 Brand Identity & Design System

one flow adheres strictly to the **onebiz design system (v2.0)**:

- **Prose Naming**: Always lowercase in prose (**one flow**, **onebiz**). Technical identifier: `oneflow`.
- **Primary Brand Color**: `hsl(352, 82%, 52%)` / `#E81B5B` (Rose / Coral).
- **Typography**: Inter (UI font) · JetBrains Mono (Code & Technical).
- **Corner Radius**: Buttons `8px` (`rounded-lg`) · Cards `12px` (`rounded-xl`) · Inputs `6px` (`rounded-md`).
- **Dark Mode**: Native `class="dark"` with neutral surfaces (`#171717`, `#1C1C1C`).

---

## 📄 License

This software is distributed under the **GNU Affero General Public License v3.0** (AGPL-3.0). See [LICENSE.txt](./LICENSE.txt) for full terms.

*Maintained by Sohan A · © 2026 one flow · Part of the onebiz Platform.*
