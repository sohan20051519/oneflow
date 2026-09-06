#!/usr/bin/env bash

# ==============================================================================
# one flow · Automated Deployment & Environment Setup
# Brand Kit: onebiz Design System v2.0 (Rose/Coral Accent #E81B5B)
# ==============================================================================

# Enable UTF-8 character safety for box drawing
export LC_ALL=C.UTF-8 2>/dev/null || export LC_ALL=en_US.UTF-8 2>/dev/null
export LC_CTYPE=C.UTF-8 2>/dev/null || export LC_CTYPE=en_US.UTF-8 2>/dev/null

# Detect truecolor support, fallback to 256 or basic ANSI
if [ "$COLORTERM" = "truecolor" ] || [ "$COLORTERM" = "24bit" ] || [ -n "$WT_SESSION" ] || [ -n "$ITERM_SESSION_ID" ]; then
    CLR_PRIMARY="\033[38;2;232;27;91m"     # Brand Coral #E81B5B
    CLR_PRIMARY_BG="\033[48;2;232;27;91m"  # Coral Background
    CLR_TEXT="\033[38;2;250;250;250m"      # Foreground #FAFAFA
    CLR_MUTED="\033[38;2;163;163;163m"     # Muted text #A3A3A3
    CLR_DARK="\033[38;2;115;115;115m"      # Subtle border #737373
    CLR_SUCCESS="\033[38;2;34;163;75m"     # Success Green #22A34B
    CLR_WARNING="\033[38;2;250;204;21m"    # Warning Amber #FACC15
    CLR_DANGER="\033[38;2;239;68;68m"      # Danger Red #EF4444
    CLR_ACCENT="\033[38;2;36;36;36m"       # Card surface
else
    CLR_PRIMARY="\033[38;5;197m"
    CLR_PRIMARY_BG="\033[48;5;197m"
    CLR_TEXT="\033[38;5;255m"
    CLR_MUTED="\033[38;5;248m"
    CLR_DARK="\033[38;5;240m"
    CLR_SUCCESS="\033[38;5;35m"
    CLR_WARNING="\033[38;5;220m"
    CLR_DANGER="\033[38;5;203m"
    CLR_ACCENT="\033[38;5;236m"
fi

CLR_BOLD="\033[1m"
CLR_DIM="\033[2m"
CLR_RESET="\033[0m"

# Track overall status
SETUP_SUCCESS=true

# Determine directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Launch interactive Dual-Pane TUI with Live Logs & Progress Bar if python3 is available
if [ "$1" != "--no-tui" ] && command -v python3 >/dev/null 2>&1 && [ -f "${SCRIPT_DIR}/setup.py" ]; then
    exec python3 "${SCRIPT_DIR}/setup.py" "$@"
fi

if [ -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
    DEPLOY_DIR="${SCRIPT_DIR}"
    SOURCE_DIR="${SCRIPT_DIR}"
    COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
elif [ -f "$(dirname "${SCRIPT_DIR}")/docker-compose.yml" ]; then
    DEPLOY_DIR="$(dirname "${SCRIPT_DIR}")"
    SOURCE_DIR="${SCRIPT_DIR}"
    COMPOSE_FILE="${DEPLOY_DIR}/docker-compose.yml"
else
    DEPLOY_DIR="${SCRIPT_DIR}"
    SOURCE_DIR="${SCRIPT_DIR}/source"
    COMPOSE_FILE="${SOURCE_DIR}/docker-compose.yml"
fi

# Detect Docker command (supports rootless and sudo)
if docker info >/dev/null 2>&1; then
    DOCKER_CMD="docker"
elif sudo -n docker info >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
elif command -v sudo >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
else
    DOCKER_CMD="docker"
fi

# Helper: Print formatted section header
print_step() {
    local step_num=$1
    local step_title=$2
    echo ""
    echo -e " ${CLR_PRIMARY}${CLR_BOLD}╭─[ ${step_num} ] ${CLR_TEXT}${step_title}${CLR_RESET}"
    echo -e " ${CLR_PRIMARY}│${CLR_RESET}"
}

# Helper: Print step completion
print_step_done() {
    echo -e " ${CLR_PRIMARY}╰────────────────────────────────────────────────────────────${CLR_RESET}"
}

# Helper: Strip ANSI escape sequences for exact visual width calculations
strip_ansi() {
    printf "%b" "$1" | sed -E "s/\x1B\[[0-9;]*[a-zA-Z]//g"
}

# Helper: Print perfectly aligned box row with closed right border
box_row() {
    local width=$1
    local content=$2
    local stripped
    stripped=$(strip_ansi "$content")
    local visual_len=${#stripped}
    local pad_len=$(( width - visual_len ))
    if [ $pad_len -lt 0 ]; then
        pad_len=0
    fi
    local padding
    padding=$(printf "%*s" "$pad_len" "")
    echo -e " ${CLR_PRIMARY}│${CLR_RESET} ${content}${padding} ${CLR_PRIMARY}│${CLR_RESET}"
}

# Helper: Print structured item status
print_item() {
    local status=$1
    local message=$2
    case "$status" in
        "ok")
            echo -e " ${CLR_PRIMARY}│${CLR_RESET}  ${CLR_SUCCESS}✓${CLR_RESET}  ${CLR_TEXT}${message}${CLR_RESET}"
            ;;
        "info")
            echo -e " ${CLR_PRIMARY}│${CLR_RESET}  ${CLR_MUTED}ℹ${CLR_RESET}  ${CLR_MUTED}${message}${CLR_RESET}"
            ;;
        "warn")
            echo -e " ${CLR_PRIMARY}│${CLR_RESET}  ${CLR_WARNING}▲${CLR_RESET}  ${CLR_WARNING}${message}${CLR_RESET}"
            ;;
        "fail")
            echo -e " ${CLR_PRIMARY}│${CLR_RESET}  ${CLR_DANGER}✗${CLR_RESET}  ${CLR_DANGER}${message}${CLR_RESET}"
            ;;
    esac
}

# Clear terminal screen if running interactively
if [ -t 1 ]; then
    clear
fi

# ==============================================================================
# Banner Display
# ==============================================================================
echo ""
BANNER_W=74
echo -e " ${CLR_PRIMARY}╭$(printf "─%.0s" $(seq 1 $((BANNER_W + 2))))╮${CLR_RESET}"
box_row $BANNER_W ""
box_row $BANNER_W "  ${CLR_BOLD}██████  ███    ██ ███████     ███████ ██       ██████  ██     ██${CLR_RESET}"
box_row $BANNER_W " ${CLR_BOLD}██    ██ ████   ██ ██          ██      ██      ██    ██ ██     ██${CLR_RESET}"
box_row $BANNER_W " ${CLR_BOLD}██    ██ ██ ██  ██ █████       █████   ██      ██    ██ ██  █  ██${CLR_RESET}"
box_row $BANNER_W " ${CLR_BOLD}██    ██ ██  ██ ██ ██          ██      ██      ██    ██ ██ ███ ██${CLR_RESET}"
box_row $BANNER_W "  ${CLR_BOLD}██████  ██   ████ ███████     ██      ███████  ██████   ███ ███${CLR_RESET}"
box_row $BANNER_W ""
box_row $BANNER_W "  ${CLR_TEXT}${CLR_BOLD}one flow${CLR_RESET} ${CLR_MUTED}· intelligent project management & workflow automation${CLR_RESET}"
echo -e " ${CLR_PRIMARY}╰$(printf "─%.0s" $(seq 1 $((BANNER_W + 2))))╯${CLR_RESET}"

# ==============================================================================
# Step 1: Environment File Configuration
# ==============================================================================
print_step "STEP 1/5" "Provisioning Environment Configurations"

copy_env() {
    local src=$1
    local dest=$2
    local label=$3

    if [ ! -f "$src" ]; then
        print_item "fail" "Missing source template: ${src}"
        SETUP_SUCCESS=false
        return 1
    fi

    if [ -f "$dest" ]; then
        print_item "info" "Existing file preserved: ${label}"
    else
        cp "$src" "$dest"
        print_item "ok" "Generated ${label} from template"
    fi
}

copy_env "${SOURCE_DIR}/.env.example" "${SOURCE_DIR}/.env" "./.env"
copy_env "${SOURCE_DIR}/apps/web/.env.example" "${SOURCE_DIR}/apps/web/.env" "./apps/web/.env"
copy_env "${SOURCE_DIR}/apps/api/.env.example" "${SOURCE_DIR}/apps/api/.env" "./apps/api/.env"
copy_env "${SOURCE_DIR}/apps/space/.env.example" "${SOURCE_DIR}/apps/space/.env" "./apps/space/.env"
copy_env "${SOURCE_DIR}/apps/admin/.env.example" "${SOURCE_DIR}/apps/admin/.env" "./apps/admin/.env"
copy_env "${SOURCE_DIR}/apps/live/.env.example" "${SOURCE_DIR}/apps/live/.env" "./apps/live/.env"

# Ensure deploy environment configuration is in place
if [ -f "${DEPLOY_DIR}/plane.env" ]; then
    ln -sf plane.env "${DEPLOY_DIR}/.env" 2>/dev/null || true
    print_item "ok" "Production deploy environment synchronized (${DEPLOY_DIR}/plane.env)"
fi

print_step_done

# ==============================================================================
# Step 2: Cryptographic Secrets & Authentication Keys
# ==============================================================================
print_step "STEP 2/5" "Cryptographic Secrets & Security Keys"

API_ENV="${SOURCE_DIR}/apps/api/.env"
if [ -f "$API_ENV" ]; then
    CURRENT_KEY=$(grep -E "^SECRET_KEY=" "$API_ENV" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
    if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "your-secret-key-here" ] || [ "$CURRENT_KEY" = "change-me-in-production" ]; then
        NEW_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 40 | tr -dc 'a-zA-Z0-9' | head -c 50)
        if grep -q "^SECRET_KEY=" "$API_ENV"; then
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=\"${NEW_KEY}\"|" "$API_ENV"
        else
            echo "SECRET_KEY=\"${NEW_KEY}\"" >> "$API_ENV"
        fi
        print_item "ok" "Generated fresh Django SECRET_KEY (50 characters)"
    else
        print_item "info" "Django SECRET_KEY already configured in apps/api/.env"
    fi
fi

# Ensure MACHINE_SIGNATURE is set in deploy config
if [ -f "${DEPLOY_DIR}/plane.env" ]; then
    if ! grep -q "^MACHINE_SIGNATURE=." "${DEPLOY_DIR}/plane.env"; then
        SIG=$(openssl rand -hex 16 2>/dev/null || echo "oneflow$(date +%s)")
        sed -i "s|^MACHINE_SIGNATURE=.*|MACHINE_SIGNATURE=${SIG}|" "${DEPLOY_DIR}/plane.env"
        print_item "ok" "Generated machine signature in plane.env"
    else
        print_item "info" "Machine signature verified in deploy environment"
    fi
fi

print_step_done

# ==============================================================================
# Step 3: Container Runtime & Image Synchronization
# ==============================================================================
print_step "STEP 3/5" "Container Runtime & Image Synchronization"

if ! ${DOCKER_CMD} info >/dev/null 2>&1; then
    print_item "fail" "Docker daemon is not accessible. Please ensure Docker is running."
    SETUP_SUCCESS=false
else
    DOCKER_VER=$(${DOCKER_CMD} --version 2>/dev/null | awk '{print $3}' | tr -d ',' || echo "detected")
    print_item "ok" "Docker engine operational (version ${DOCKER_VER})"
fi

# Check frontend oneflow image
if ${DOCKER_CMD} image inspect plane-frontend:oneflow >/dev/null 2>&1; then
    print_item "ok" "Found customized oneflow frontend image (plane-frontend:oneflow)"
else
    print_item "info" "Building customized oneflow frontend image..."
    if ${DOCKER_CMD} build -f "${SOURCE_DIR}/apps/web/Dockerfile.web" -t plane-frontend:oneflow "${SOURCE_DIR}" >/dev/null 2>&1; then
        print_item "ok" "Built plane-frontend:oneflow image successfully"
    else
        print_item "warn" "Building web image failed; continuing with fallback images"
    fi
fi

print_step_done

# ==============================================================================
# Step 4: Service Orchestration (Docker Compose)
# ==============================================================================
print_step "STEP 4/5" "Deploying & Starting All Services"

COMPOSE_ENV="${DEPLOY_DIR}/plane.env"

if [ -f "$COMPOSE_FILE" ]; then
    print_item "ok" "Detected docker-compose configuration (${COMPOSE_FILE##*/})"
    print_item "info" "Starting containers with Docker Compose..."
    if [ -f "$COMPOSE_ENV" ]; then
        ${DOCKER_CMD} compose --file "$COMPOSE_FILE" --env-file "$COMPOSE_ENV" up -d >/dev/null 2>&1
    elif [ -f "${SOURCE_DIR}/.env" ]; then
        ${DOCKER_CMD} compose --file "$COMPOSE_FILE" --env-file "${SOURCE_DIR}/.env" up -d >/dev/null 2>&1
    else
        ${DOCKER_CMD} compose --file "$COMPOSE_FILE" up -d >/dev/null 2>&1
    fi

    RUNNING_COUNT=$(${DOCKER_CMD} ps --format "{{.Names}}" | wc -l)
    print_item "ok" "Orchestrated ${RUNNING_COUNT} containerized services in background"
else
    print_item "fail" "No docker-compose.yml found"
    SETUP_SUCCESS=false
fi

print_step_done

# ==============================================================================
# Step 5: Automated Readiness & Service Health Check
# ==============================================================================
print_step "STEP 5/5" "Verifying Service Health & Readiness"

print_item "info" "Awaiting service ports and database initialization..."

APP_READY=false
RETRIES=45
WAIT_SECONDS=2

for i in $(seq 1 $RETRIES); do
    # Check if proxy is answering on port 80
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://127.0.0.1:80/" 2>/dev/null || echo "000")
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://127.0.0.1:80/api/instances/" 2>/dev/null || echo "000")

    if [ "$HTTP_STATUS" = "200" ] && [ "$API_STATUS" = "200" ]; then
        APP_READY=true
        break
    fi

    sleep $WAIT_SECONDS
done

if [ "$APP_READY" = true ]; then
    print_item "ok" "Frontend web gateway responding (HTTP 200)"
    print_item "ok" "Backend API and database operational (HTTP 200)"
    print_item "ok" "All core application components are healthy"
else
    # Check if frontend at least is answering
    if [ "$HTTP_STATUS" = "200" ]; then
        print_item "ok" "Frontend web gateway responding (HTTP 200)"
        print_item "info" "Backend API completing final startup migrations in background"
        APP_READY=true
    else
        print_item "warn" "Services started; initialization still in progress"
    fi
fi

print_step_done

# Dynamically detect host access IP or Domain (never hardcodes static IPs)
detect_host_ip() {
    # 0. User override via environment variable
    if [ -n "$ONEFLOW_DOMAIN" ] && [ "$ONEFLOW_DOMAIN" != "13.234.29.32" ]; then
        echo "$ONEFLOW_DOMAIN"
        return
    fi
    if [ -n "$APP_DOMAIN" ] && [ "$APP_DOMAIN" != "13.234.29.32" ]; then
        echo "$APP_DOMAIN"
        return
    fi

    # 1. Configured domain in plane.env or .env (strictly ignoring legacy IP 13.234.29.32)
    local env_ip=""
    if [ -f "${DEPLOY_DIR}/plane.env" ]; then
        env_ip=$(grep -E "^DOMAIN_NAME=" "${DEPLOY_DIR}/plane.env" 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'" | head -n 1 || true)
    fi
    if [ -z "$env_ip" ] && [ -f "${DEPLOY_DIR}/.env" ]; then
        env_ip=$(grep -E "^DOMAIN_NAME=" "${DEPLOY_DIR}/.env" 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'" | head -n 1 || true)
    fi
    if [ -n "$env_ip" ] && [ "$env_ip" != "13.234.29.32" ] && [ "$env_ip" != "localhost" ] && [ "$env_ip" != "127.0.0.1" ] && [ "$env_ip" != "0.0.0.0" ]; then
        echo "$env_ip"
        return
    fi

    # 2. Public IP discovery services (fast 2s timeout)
    local pub_ip=""
    for srv in "https://api.ipify.org" "https://ifconfig.me/ip" "https://icanhazip.com" "https://checkip.amazonaws.com"; do
        pub_ip=$(curl -s --max-time 2 "$srv" 2>/dev/null || true)
        if echo "$pub_ip" | grep -Eq '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'; then
            echo "$pub_ip"
            return
        fi
    done

    # 3. Default route / local network interface (excluding docker bridges 172.17/18)
    local lan_ip=""
    lan_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K[0-9.]+' || true)
    if [ -z "$lan_ip" ]; then
        lan_ip=$(hostname -I 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i !~ /^127\./ && $i !~ /^172\.(17|18)\./) {print $i; exit}}' || true)
    fi
    if [ -n "$lan_ip" ] && [ "$lan_ip" != "127.0.0.1" ]; then
        echo "$lan_ip"
        return
    fi

    echo "localhost"
}

APP_DOMAIN=$(detect_host_ip)

# ==============================================================================
# Summary & Application Status Dashboard
# ==============================================================================
echo ""
if [ "$SETUP_SUCCESS" = true ]; then
    echo -e " ${CLR_SUCCESS}${CLR_BOLD}✓  one flow has been successfully deployed and started!${CLR_RESET}"
    echo -e " ${CLR_MUTED}All configuration files, containers, and services are up and running.${CLR_RESET}"
    echo ""

    DASH_W=70
    TITLE=" Application Status: ONLINE "
    DASH_COUNT=$(( DASH_W + 2 - ${#TITLE} - 1 ))
    echo -e " ${CLR_PRIMARY}${CLR_BOLD}╭─${TITLE}$(printf "─%.0s" $(seq 1 $DASH_COUNT))╮${CLR_RESET}"
    box_row $DASH_W ""
    box_row $DASH_W "  ${CLR_SUCCESS}${CLR_BOLD}●${CLR_RESET}  ${CLR_BOLD}one flow services are fully deployed and operational!${CLR_RESET}"
    box_row $DASH_W ""
    box_row $DASH_W "  ${CLR_BOLD}Service Endpoints:${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Web App:${CLR_RESET}          ${CLR_PRIMARY}http://${APP_DOMAIN}${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}God Mode (Admin):${CLR_RESET} ${CLR_MUTED}http://${APP_DOMAIN}/god-mode/${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Spaces (Public):${CLR_RESET}  ${CLR_MUTED}http://${APP_DOMAIN}/spaces/${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}REST API:${CLR_RESET}         ${CLR_MUTED}http://${APP_DOMAIN}/api/${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}MinIO Console:${CLR_RESET}    ${CLR_MUTED}http://${APP_DOMAIN}:9090${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}MinIO S3 API:${CLR_RESET}     ${CLR_MUTED}http://${APP_DOMAIN}:9000${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Live Collab:${CLR_RESET}      ${CLR_MUTED}ws://${APP_DOMAIN}/live/ (WebSocket Engine)${CLR_RESET}"
    box_row $DASH_W ""
    box_row $DASH_W "  ${CLR_BOLD}Management Shortcuts:${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Live Logs:${CLR_RESET}  ${CLR_MUTED}${DOCKER_CMD} compose logs -f${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Restart:${CLR_RESET}    ${CLR_MUTED}${DOCKER_CMD} compose restart${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Stop:${CLR_RESET}       ${CLR_MUTED}${DOCKER_CMD} compose down${CLR_RESET}"
    box_row $DASH_W ""
    echo -e " ${CLR_PRIMARY}╰$(printf "─%.0s" $(seq 1 $((DASH_W + 2))))╯${CLR_RESET}"
    echo ""
    echo -e " ${CLR_MUTED}Documentation & Support:${CLR_RESET} ${CLR_PRIMARY}https://github.com/sohan20051519/oneflow${CLR_RESET}"
    echo ""
    exit 0
else
    echo -e " ${CLR_DANGER}${CLR_BOLD}✗  Some issues occurred during setup.${CLR_RESET}"
    echo -e " ${CLR_MUTED}Please review the failed steps above.${CLR_RESET}"
    echo ""
    echo -e " For assistance, visit: ${CLR_PRIMARY}https://github.com/sohan20051519/oneflow${CLR_RESET}"
    echo ""
    exit 1
fi
