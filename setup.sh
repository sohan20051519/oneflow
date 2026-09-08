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
    CLR_CYAN="\033[38;2;56;189;248m"       # Info Accent #38BDF8
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
    CLR_CYAN="\033[38;5;81m"
    CLR_ACCENT="\033[38;5;236m"
fi

CLR_BOLD="\033[1m"
CLR_DIM="\033[2m"
CLR_RESET="\033[0m"

# Track overall status
SETUP_SUCCESS=true

# Global failure tracking arrays for exact error diagnostics
declare -a FAIL_STEPS=()
declare -a FAIL_COMMANDS=()
declare -a FAIL_EXITCODES=()
declare -a FAIL_DETAILS=()

record_failure() {
    local step_title="$1"
    local command_str="$2"
    local exit_code="$3"
    local detail_text="$4"
    FAIL_STEPS+=("$step_title")
    FAIL_COMMANDS+=("$command_str")
    FAIL_EXITCODES+=("$exit_code")
    FAIL_DETAILS+=("$detail_text")
    SETUP_SUCCESS=false
}

print_exact_error() {
    local title="$1"
    local details="$2"
    echo ""
    echo -e " ${CLR_DANGER}${CLR_BOLD}┌──[ EXACT ERROR: ${title} ]─────────────────────────────────${CLR_RESET}"
    if [ -n "$details" ]; then
        while IFS= read -r err_line; do
            echo -e " ${CLR_DANGER}│${CLR_RESET}  ${err_line}"
        done <<< "$details"
    fi
    echo -e " ${CLR_DANGER}└──$(printf '─%.0s' $(seq 1 60))${CLR_RESET}"
    echo ""
}

# Determine directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# If plane.env is not in DEPLOY_DIR but is in parent directory, resolve DEPLOY_DIR to parent
if [ ! -f "${DEPLOY_DIR}/plane.env" ] && [ -f "$(dirname "${DEPLOY_DIR}")/plane.env" ]; then
    DEPLOY_DIR="$(dirname "${DEPLOY_DIR}")"
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

# Pre-authenticate sudo cleanly in standard terminal mode
if ! docker info >/dev/null 2>&1 && command -v sudo >/dev/null 2>&1; then
    if ! sudo -n docker info >/dev/null 2>&1; then
        echo ""
        echo -e " ${CLR_PRIMARY}${CLR_BOLD}●${CLR_RESET} ${CLR_BOLD}Sudo privileges required for Docker container management.${CLR_RESET}"
        echo -e "   Please enter your sudo password if prompted below:"
        sudo -v || exit 1
        echo ""
    fi
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
    local inner_width=$(( width - 4 ))
    local pad_len=$(( inner_width - visual_len ))
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

# Dynamically detect host access IP or Domain
detect_host_ip() {
    # 0. User override via environment variable
    if [ -n "$ONEFLOW_DOMAIN" ] && [ "$ONEFLOW_DOMAIN" != "localhost" ] && [ "$ONEFLOW_DOMAIN" != "127.0.0.1" ]; then
        echo "$ONEFLOW_DOMAIN"
        return
    fi
    if [ -n "$APP_DOMAIN" ] && [ "$APP_DOMAIN" != "localhost" ] && [ "$APP_DOMAIN" != "127.0.0.1" ]; then
        echo "$APP_DOMAIN"
        return
    fi

    # 1. Configured domain in plane.env or .env
    local env_ip=""
    if [ -f "${DEPLOY_DIR}/plane.env" ]; then
        env_ip=$(grep -E "^(ONEFLOW_DOMAIN|DOMAIN_NAME)=" "${DEPLOY_DIR}/plane.env" 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'" | head -n 1 || true)
    fi
    if [ -z "$env_ip" ] && [ -f "${SOURCE_DIR}/.env" ]; then
        env_ip=$(grep -E "^(ONEFLOW_DOMAIN|DOMAIN_NAME)=" "${SOURCE_DIR}/.env" 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'" | head -n 1 || true)
    fi
    if [ -z "$env_ip" ] && [ -f "${DEPLOY_DIR}/.env" ]; then
        env_ip=$(grep -E "^(ONEFLOW_DOMAIN|DOMAIN_NAME)=" "${DEPLOY_DIR}/.env" 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'" | head -n 1 || true)
    fi
    if [ -n "$env_ip" ] && [ "$env_ip" != "localhost" ] && [ "$env_ip" != "127.0.0.1" ] && [ "$env_ip" != "0.0.0.0" ]; then
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

# Parse Command-Line Arguments
CLI_DOMAIN=""
USE_TUI=false
NO_PROMPT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain|-d)
            CLI_DOMAIN="$2"
            shift 2
            ;;
        --domain=*)
            CLI_DOMAIN="${1#*=}"
            shift
            ;;
        --tui)
            USE_TUI=true
            shift
            ;;
        --no-tui)
            USE_TUI=false
            shift
            ;;
        --no-prompt)
            NO_PROMPT=true
            shift
            ;;
        -h|--help)
            echo "one flow · Deployment Setup Script"
            echo ""
            echo "Usage: ./setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --domain <URL|IP>   Specify deployment domain or IP without prompting"
            echo "      --tui               Launch dual-pane interactive Python TUI"
            echo "      --no-tui            Run in standard terminal mode (default)"
            echo "      --no-prompt         Use existing/detected domain without interactive prompt"
            echo "  -h, --help              Show this help message"
            echo ""
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

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
# Step 0: Domain Configuration (Interactive prompt before setup begins)
# ==============================================================================

# Determine default domain candidate
DETECTED_RAW=$(detect_host_ip)
DETECTED_RAW="${DETECTED_RAW%/}"

if [[ "$DETECTED_RAW" =~ ^https?:// ]]; then
    DEFAULT_DOMAIN="$DETECTED_RAW"
elif [[ "$DETECTED_RAW" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$ ]] || [ "$DETECTED_RAW" = "localhost" ] || [[ "$DETECTED_RAW" =~ ^localhost:[0-9]+$ ]]; then
    DEFAULT_DOMAIN="http://${DETECTED_RAW}"
elif [ -n "$DETECTED_RAW" ]; then
    DEFAULT_DOMAIN="https://${DETECTED_RAW}"
else
    DEFAULT_DOMAIN="http://localhost"
fi

CHOSEN_INPUT=""

if [ -n "$CLI_DOMAIN" ]; then
    CHOSEN_INPUT="$CLI_DOMAIN"
elif [ "$NO_PROMPT" = true ] || [ ! -t 0 ]; then
    CHOSEN_INPUT="$DEFAULT_DOMAIN"
else
    echo ""
    echo -e " ${CLR_PRIMARY}${CLR_BOLD}╭─[ DEPLOYMENT DOMAIN CONFIGURATION ]────────────────────────╮${CLR_RESET}"
    echo -e " ${CLR_PRIMARY}│${CLR_RESET}  ${CLR_BOLD}Enter the public domain or IP address for OneFlow.${CLR_RESET}        ${CLR_PRIMARY}│${CLR_RESET}"
    echo -e " ${CLR_PRIMARY}│${CLR_RESET}  ${CLR_MUTED}Examples:${CLR_RESET}                                                 ${CLR_PRIMARY}│${CLR_RESET}"
    echo -e " ${CLR_PRIMARY}│${CLR_RESET}    • ${CLR_CYAN}https://oneflow.cubeone.in${CLR_RESET}  (Production with SSL)       ${CLR_PRIMARY}│${CLR_RESET}"
    echo -e " ${CLR_PRIMARY}│${CLR_RESET}    • ${CLR_CYAN}http://13.234.29.32${CLR_RESET}         (Staging / Public IP)       ${CLR_PRIMARY}│${CLR_RESET}"
    echo -e " ${CLR_PRIMARY}│${CLR_RESET}    • ${CLR_CYAN}http://localhost${CLR_RESET}            (Local Development)         ${CLR_PRIMARY}│${CLR_RESET}"
    echo -e " ${CLR_PRIMARY}╰────────────────────────────────────────────────────────────╯${CLR_RESET}"
    echo ""
    read -r -p " Enter Domain [default: ${DEFAULT_DOMAIN}]: " USER_DOMAIN_INPUT
    CHOSEN_INPUT="${USER_DOMAIN_INPUT}"
fi

# Normalize domain input
CHOSEN_INPUT=$(echo "$CHOSEN_INPUT" | xargs)
CHOSEN_INPUT="${CHOSEN_INPUT%/}"

if [ -z "$CHOSEN_INPUT" ]; then
    CHOSEN_INPUT="${DEFAULT_DOMAIN}"
fi

if [[ "$CHOSEN_INPUT" =~ ^https?:// ]]; then
    FINAL_ORIGIN="$CHOSEN_INPUT"
elif [[ "$CHOSEN_INPUT" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$ ]] || [ "$CHOSEN_INPUT" = "localhost" ] || [[ "$CHOSEN_INPUT" =~ ^localhost:[0-9]+$ ]]; then
    FINAL_ORIGIN="http://${CHOSEN_INPUT}"
else
    FINAL_ORIGIN="https://${CHOSEN_INPUT}"
fi

FINAL_HOST=$(echo "$FINAL_ORIGIN" | sed -E 's|^https?://||; s|/.*||; s|:[0-9]+$||')
FINAL_SCHEME=$(echo "$FINAL_ORIGIN" | grep -oE '^https?')

# Export canonical environment variables immediately
export ONEFLOW_DOMAIN="${FINAL_ORIGIN}"
export DOMAIN_NAME="${FINAL_HOST}"
export APP_DOMAIN="${FINAL_HOST}"
export WEB_URL="${FINAL_ORIGIN}"
export APP_PROTOCOL="${FINAL_SCHEME}"
export ONEFLOW_DOMAIN_CONFIGURED=1

# ---------------------------------------------------------------------------
# Comprehensive domain sync — updates EVERY domain-dependent variable across
# ALL env files (inside and outside containers) whenever the user sets a domain.
# ---------------------------------------------------------------------------

# Helper: upsert a key=value pair in an env file (update if exists, append if not)
_upsert_env() {
    local file="$1" key="$2" val="$3"
    [ -f "$file" ] || return 0
    if grep -q "^${key}=" "$file" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${val}|" "$file"
    else
        echo "${key}=${val}" >> "$file"
    fi
}

# ---------------------------------------------------------------------------
# sync_domain_in_file <env_file>
#   Updates every domain-sensitive key in a single env file.
#   Safe to call on any env file — keys not present are silently skipped
#   unless they are core identity keys (ONEFLOW_DOMAIN / DOMAIN_NAME) which
#   are always upserted.
# ---------------------------------------------------------------------------
sync_domain_in_file() {
    local f="$1"
    [ -f "$f" ] || return 0

    # ── Core identity keys (always upserted) ────────────────────────────────
    _upsert_env "$f" "ONEFLOW_DOMAIN"  "${FINAL_ORIGIN}"
    _upsert_env "$f" "DOMAIN_NAME"     "${FINAL_HOST}"

    # ── Domain alias keys (updated only if already present) ─────────────────
    grep -q "^APP_DOMAIN="   "$f" 2>/dev/null && sed -i "s|^APP_DOMAIN=.*|APP_DOMAIN=${FINAL_HOST}|"   "$f"
    grep -q "^DOMAIN="       "$f" 2>/dev/null && sed -i "s|^DOMAIN=.*|DOMAIN=${FINAL_HOST}|"           "$f"
    grep -q "^APP_PROTOCOL=" "$f" 2>/dev/null && sed -i "s|^APP_PROTOCOL=.*|APP_PROTOCOL=${FINAL_SCHEME}|" "$f"

    # ── Public URL keys ──────────────────────────────────────────────────────
    # WEB_URL — keep as literal value (not reference) so containers see it
    grep -q "^WEB_URL=" "$f" 2>/dev/null && sed -i "s|^WEB_URL=.*|WEB_URL=${FINAL_ORIGIN}|" "$f"

    # ── CORS / CSRF ──────────────────────────────────────────────────────────
    if grep -q "^CORS_ALLOWED_ORIGINS=" "$f" 2>/dev/null; then
        local cors_val="${FINAL_ORIGIN}"
        # If HTTPS domain, also allow the plain http variant for local API calls
        if [ "$FINAL_SCHEME" = "https" ]; then
            cors_val="${FINAL_ORIGIN},http://${FINAL_HOST}"
        fi
        sed -i "s|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=${cors_val}|" "$f"
    fi
    if grep -q "^CSRF_TRUSTED_ORIGINS=" "$f" 2>/dev/null; then
        sed -i "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=${FINAL_ORIGIN}|" "$f"
    fi

    # ── Webhook host allowlist ────────────────────────────────────────────────
    if grep -q "^WEBHOOK_ALLOWED_HOSTS=" "$f" 2>/dev/null; then
        sed -i "s|^WEBHOOK_ALLOWED_HOSTS=.*|WEBHOOK_ALLOWED_HOSTS=${FINAL_ORIGIN}|" "$f"
    fi

    # ── Silo / integration callback ───────────────────────────────────────────
    if grep -q "^INTEGRATION_CALLBACK_BASE_URL=" "$f" 2>/dev/null; then
        local cur_icb
        cur_icb=$(grep "^INTEGRATION_CALLBACK_BASE_URL=" "$f" | cut -d= -f2- | tr -d '"' | tr -d "'")
        # Only set when currently empty; don't overwrite a deliberately configured value
        if [ -z "$cur_icb" ]; then
            sed -i "s|^INTEGRATION_CALLBACK_BASE_URL=.*|INTEGRATION_CALLBACK_BASE_URL=${FINAL_ORIGIN}|" "$f"
        fi
    fi

    # ── SMTP domain (hostname part only, not the full origin) ─────────────────
    if grep -q "^SMTP_DOMAIN=" "$f" 2>/dev/null; then
        local cur_smtp
        cur_smtp=$(grep "^SMTP_DOMAIN=" "$f" | cut -d= -f2- | tr -d '"' | tr -d "'")
        # Only update if still set to the default placeholder
        if [ "$cur_smtp" = "0.0.0.0" ] || [ "$cur_smtp" = "example.com" ] || [ -z "$cur_smtp" ]; then
            sed -i "s|^SMTP_DOMAIN=.*|SMTP_DOMAIN=${FINAL_HOST}|" "$f"
        fi
    fi

    # ── PI OAuth redirect URI ─────────────────────────────────────────────────
    if grep -q "^PLANE_OAUTH_REDIRECT_URI=" "$f" 2>/dev/null; then
        local cur_pi
        cur_pi=$(grep "^PLANE_OAUTH_REDIRECT_URI=" "$f" | cut -d= -f2- | tr -d '"' | tr -d "'")
        if [ -z "$cur_pi" ]; then
            sed -i "s|^PLANE_OAUTH_REDIRECT_URI=.*|PLANE_OAUTH_REDIRECT_URI=${FINAL_ORIGIN}/pi/api/v1/oauth/callback/|" "$f"
        fi
    fi

    # ── Keycloak / OIDC redirect URIs ────────────────────────────────────────
    if grep -q "^KEYCLOAK_REDIRECT_URI=" "$f" 2>/dev/null; then
        sed -i "s|^KEYCLOAK_REDIRECT_URI=.*|KEYCLOAK_REDIRECT_URI=${FINAL_ORIGIN}/auth/oidc/callback/|" "$f"
    fi
    if grep -q "^KEYCLOAK_POST_LOGOUT_REDIRECT_URI=" "$f" 2>/dev/null; then
        sed -i "s|^KEYCLOAK_POST_LOGOUT_REDIRECT_URI=.*|KEYCLOAK_POST_LOGOUT_REDIRECT_URI=${FINAL_ORIGIN}/|" "$f"
    fi

    # ── Proxy SITE_ADDRESS (port directive for Caddy) ─────────────────────────
    if grep -q "^SITE_ADDRESS=" "$f" 2>/dev/null; then
        if [ "$FINAL_SCHEME" = "https" ]; then
            sed -i "s|^SITE_ADDRESS=.*|SITE_ADDRESS=${FINAL_HOST}|" "$f"
        else
            sed -i "s|^SITE_ADDRESS=.*|SITE_ADDRESS=:80|" "$f"
        fi
    fi
}

# ---------------------------------------------------------------------------
# sync_all_domain_vars — applies sync_domain_in_file to EVERY env file
# ---------------------------------------------------------------------------
sync_all_domain_vars() {
    local synced=0

    # Primary deploy-level env files (outside containers)
    for env_f in \
        "${DEPLOY_DIR}/plane.env" \
        "${DEPLOY_DIR}/.env" \
        "$(dirname "${DEPLOY_DIR}")/plane.env" \
        "$(dirname "${DEPLOY_DIR}")/.env" \
        "${SOURCE_DIR}/.env"
    do
        if [ -f "$env_f" ]; then
            sync_domain_in_file "$env_f"
            synced=$((synced + 1))
        fi
    done

    # .config.env (used by the plane CLI / installer bookkeeping)
    if [ -f "${DEPLOY_DIR}/.config.env" ]; then
        sync_domain_in_file "${DEPLOY_DIR}/.config.env"
        synced=$((synced + 1))
    fi

    # App-level env files (source tree — these get bind-mounted or baked into images)
    local app_env
    for app_env in \
        "${SOURCE_DIR}/apps/api/.env" \
        "${SOURCE_DIR}/apps/web/.env" \
        "${SOURCE_DIR}/apps/space/.env" \
        "${SOURCE_DIR}/apps/admin/.env" \
        "${SOURCE_DIR}/apps/live/.env"
    do
        if [ -f "$app_env" ]; then
            sync_domain_in_file "$app_env"
            synced=$((synced + 1))
        fi
    done

    # Deployment template variables files
    for tpl_env in \
        "${SOURCE_DIR}/deployments/cli/community/variables.env" \
        "${SOURCE_DIR}/deployments/aio/community/variables.env"
    do
        if [ -f "$tpl_env" ]; then
            sync_domain_in_file "$tpl_env"
            synced=$((synced + 1))
        fi
    done

    echo -e " ${CLR_SUCCESS}✓${CLR_RESET}  Domain propagated to ${CLR_BOLD}${synced}${CLR_RESET} environment files"
}

# Run the comprehensive sync immediately after domain is determined
sync_all_domain_vars

echo ""
echo -e " ${CLR_SUCCESS}✓${CLR_RESET}  ${CLR_BOLD}Deployment domain configured:${CLR_RESET} ${CLR_PRIMARY}${FINAL_ORIGIN}${CLR_RESET} ${CLR_MUTED}(host: ${FINAL_HOST}, scheme: ${FINAL_SCHEME})${CLR_RESET}"
echo -e " ${CLR_MUTED}Starting automated deployment setup...${CLR_RESET}"
echo ""

# Delegate to interactive Python TUI only if explicitly requested
if [ "$USE_TUI" = true ] && command -v python3 >/dev/null 2>&1 && [ -f "${SOURCE_DIR}/setup.py" ]; then
    exec python3 "${SOURCE_DIR}/setup.py" --domain "${FINAL_ORIGIN}" "$@"
fi

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
        record_failure "STEP 1: Provisioning Environment Configurations" "copy_env $src $dest" 1 "Missing source template file: ${src}"
        SETUP_SUCCESS=false
        return 1
    fi

    if [ -f "$dest" ]; then
        print_item "info" "Existing file preserved: ${label}"
    else
        local copy_err
        copy_err=$(cp "$src" "$dest" 2>&1)
        if [ $? -eq 0 ]; then
            print_item "ok" "Generated ${label} from template"
        else
            print_item "fail" "Failed to create ${label}: ${copy_err}"
            record_failure "STEP 1: Provisioning Environment Configurations" "cp $src $dest" 1 "$copy_err"
            SETUP_SUCCESS=false
        fi
    fi
}

copy_env "${SOURCE_DIR}/.env.example" "${SOURCE_DIR}/.env" "./.env"
copy_env "${SOURCE_DIR}/apps/web/.env.example" "${SOURCE_DIR}/apps/web/.env" "./apps/web/.env"
copy_env "${SOURCE_DIR}/apps/api/.env.example" "${SOURCE_DIR}/apps/api/.env" "./apps/api/.env"
copy_env "${SOURCE_DIR}/apps/space/.env.example" "${SOURCE_DIR}/apps/space/.env" "./apps/space/.env"
copy_env "${SOURCE_DIR}/apps/admin/.env.example" "${SOURCE_DIR}/apps/admin/.env" "./apps/admin/.env"
copy_env "${SOURCE_DIR}/apps/live/.env.example" "${SOURCE_DIR}/apps/live/.env" "./apps/live/.env"

# Auto-sanitize apps/api/.env to eliminate unexpanded variables and localhost endpoints
if [ -f "${SOURCE_DIR}/apps/api/.env" ]; then
    api_env_path="${SOURCE_DIR}/apps/api/.env"
    if grep -q "DATABASE_URL=.*" "$api_env_path"; then
        sed -i 's|^DATABASE_URL=.*|DATABASE_URL="postgresql://plane:plane@plane-db:5432/plane"|' "$api_env_path"
        print_item "ok" "Fixed DATABASE_URL container endpoint in apps/api/.env"
    fi
    if grep -q "REDIS_URL=.*" "$api_env_path"; then
        sed -i 's|^REDIS_URL=.*|REDIS_URL="redis://plane-redis:6379/"|' "$api_env_path"
        print_item "ok" "Fixed REDIS_URL container endpoint in apps/api/.env"
    fi
    if ! grep -q "^CELERY_BROKER_URL=" "${SOURCE_DIR}/apps/api/.env"; then
        echo 'CELERY_BROKER_URL="redis://plane-redis:6379/1"' >> "${SOURCE_DIR}/apps/api/.env"
        print_item "ok" "Configured Redis as Celery broker in apps/api/.env"
    else
        sed -i 's|^CELERY_BROKER_URL=.*|CELERY_BROKER_URL="redis://plane-redis:6379/1"|' "${SOURCE_DIR}/apps/api/.env"
    fi
    if ! grep -q "^GUNICORN_WORKERS=" "${SOURCE_DIR}/apps/api/.env"; then
        echo 'GUNICORN_WORKERS="1"' >> "${SOURCE_DIR}/apps/api/.env"
    else
        sed -i 's|^GUNICORN_WORKERS=.*|GUNICORN_WORKERS="1"|' "${SOURCE_DIR}/apps/api/.env"
    fi

    # Clear unexposed dev ports in container base URLs so Caddy handles all reverse proxying
    sed -i 's|^ADMIN_BASE_URL=.*:3001.*|ADMIN_BASE_URL=""|' "${api_env_path}" 2>/dev/null || true
    sed -i 's|^SPACE_BASE_URL=.*:3002.*|SPACE_BASE_URL=""|' "${api_env_path}" 2>/dev/null || true
    sed -i 's|^APP_BASE_URL=.*:3000.*|APP_BASE_URL=""|' "${api_env_path}" 2>/dev/null || true
    sed -i 's|^LIVE_BASE_URL=.*:3100.*|LIVE_BASE_URL=""|' "${api_env_path}" 2>/dev/null || true
    sed -i 's|^WEB_URL=.*:3000.*|WEB_URL="http://localhost"|' "${api_env_path}" 2>/dev/null || true
fi

# Sanitize frontend .env files for reverse proxy relative URLs
for fe in admin web space; do
    if [ -f "${SOURCE_DIR}/apps/${fe}/.env" ]; then
        sed -i 's|http://localhost:8000||g; s|http://localhost:3000||g; s|http://localhost:3001||g; s|http://localhost:3002||g; s|http://localhost:3100||g' "${SOURCE_DIR}/apps/${fe}/.env"
    fi
done

# Auto-sanitize apps/live/.env for container networking
if [ -f "${SOURCE_DIR}/apps/live/.env" ]; then
    sed -i 's|http://localhost:8000|http://api:8000|g' "${SOURCE_DIR}/apps/live/.env"
    sed -i 's|^REDIS_HOST=localhost|REDIS_HOST="plane-redis"|' "${SOURCE_DIR}/apps/live/.env"
    sed -i 's|redis://localhost:6379/|redis://plane-redis:6379/|g' "${SOURCE_DIR}/apps/live/.env"
    if ! grep -q "^LIVE_SERVER_SECRET_KEY=" "${SOURCE_DIR}/apps/live/.env"; then
        echo 'LIVE_SERVER_SECRET_KEY="secret-key"' >> "${SOURCE_DIR}/apps/live/.env"
        print_item "ok" "Added LIVE_SERVER_SECRET_KEY to apps/live/.env"
    fi
fi

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

DOCKER_TEST_LOG=$(mktemp)
if ! ${DOCKER_CMD} info >"$DOCKER_TEST_LOG" 2>&1; then
    DOCKER_ERR_MSG=$(cat "$DOCKER_TEST_LOG")
    print_item "fail" "Docker daemon is not accessible"
    print_exact_error "Docker Engine Accessibility Failure" "$DOCKER_ERR_MSG"
    record_failure "STEP 3: Container Runtime" "${DOCKER_CMD} info" 1 "$DOCKER_ERR_MSG"
    SETUP_SUCCESS=false
else
    DOCKER_VER=$(${DOCKER_CMD} --version 2>/dev/null | awk '{print $3}' | tr -d ',' || echo "detected")
    print_item "ok" "Docker engine operational (version ${DOCKER_VER})"
fi
rm -f "$DOCKER_TEST_LOG"

# Check frontend oneflow image
if ${DOCKER_CMD} image inspect plane-frontend:oneflow >/dev/null 2>&1; then
    print_item "ok" "Found customized oneflow frontend image (plane-frontend:oneflow)"
else
    print_item "info" "Building customized oneflow frontend image..."
    BUILD_LOG=$(mktemp)
    if ${DOCKER_CMD} build -f "${SOURCE_DIR}/apps/web/Dockerfile.web" -t plane-frontend:oneflow "${SOURCE_DIR}" >"$BUILD_LOG" 2>&1; then
        print_item "ok" "Built plane-frontend:oneflow image successfully"
    else
        BUILD_EXIT=$?
        BUILD_ERR_SNIP=$(tail -n 35 "$BUILD_LOG")
        print_item "warn" "Building web image failed; continuing with fallback images"
        print_exact_error "Custom Frontend Build Failed (exit code ${BUILD_EXIT})" "$BUILD_ERR_SNIP"
        record_failure "STEP 3: Custom Frontend Image Build" "${DOCKER_CMD} build -f ${SOURCE_DIR}/apps/web/Dockerfile.web -t plane-frontend:oneflow ${SOURCE_DIR}" "$BUILD_EXIT" "$BUILD_ERR_SNIP"
    fi
    rm -f "$BUILD_LOG"
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

    COMPOSE_ARGS=("--file" "$COMPOSE_FILE")
    if [ -f "$COMPOSE_ENV" ]; then
        COMPOSE_ARGS+=("--env-file" "$COMPOSE_ENV")
    elif [ -f "${SOURCE_DIR}/.env" ]; then
        COMPOSE_ARGS+=("--env-file" "${SOURCE_DIR}/.env")
    fi
    COMPOSE_ARGS+=("up" "-d" "--build")

    COMPOSE_LOG=$(mktemp)
    if ${DOCKER_CMD} compose "${COMPOSE_ARGS[@]}" >"$COMPOSE_LOG" 2>&1; then
        RUNNING_COUNT=$(${DOCKER_CMD} ps --format "{{.Names}}" | wc -l)
        print_item "ok" "Orchestrated ${RUNNING_COUNT} containerized services in background"
    else
        COMPOSE_EXIT=$?
        COMPOSE_ERR=$(cat "$COMPOSE_LOG")
        print_item "fail" "Docker Compose failed to start services (exit code ${COMPOSE_EXIT})"
        print_exact_error "Docker Compose Command Failed" "$COMPOSE_ERR"
        record_failure "STEP 4: Service Orchestration" "${DOCKER_CMD} compose ${COMPOSE_ARGS[*]}" "$COMPOSE_EXIT" "$COMPOSE_ERR"
        SETUP_SUCCESS=false
    fi
    rm -f "$COMPOSE_LOG"
else
    print_item "fail" "No docker-compose.yml found"
    record_failure "STEP 4: Service Orchestration" "check $COMPOSE_FILE" 1 "Compose file not found at: ${COMPOSE_FILE}"
    SETUP_SUCCESS=false
fi

print_step_done

# ==============================================================================
# Step 5: Automated Readiness & Service Health Check
# ==============================================================================
print_step "STEP 5/5" "Verifying Service Health & Readiness"

print_item "info" "Awaiting database migrations and service readiness..."

# --- Phase 1: Wait for migrator to complete ---
MIGRATOR_OK=false
MIGRATOR_RETRIES=60
for i in $(seq 1 $MIGRATOR_RETRIES); do
    MIGRATOR_STATUS=$(${DOCKER_CMD} inspect --format='{{.State.Status}}' plane-migrator 2>/dev/null || echo "missing")
    if [ "$MIGRATOR_STATUS" = "exited" ]; then
        MIGRATOR_EXIT=$(${DOCKER_CMD} inspect --format='{{.State.ExitCode}}' plane-migrator 2>/dev/null || echo "1")
        if [ "$MIGRATOR_EXIT" = "0" ]; then
            MIGRATOR_OK=true
            print_item "ok" "Database migrations completed successfully"
        else
            MIGRATOR_LOGS=$(${DOCKER_CMD} logs --tail 40 plane-migrator 2>&1 || echo "Could not retrieve migrator logs")
            print_item "fail" "Database migrations FAILED (exit code ${MIGRATOR_EXIT})"
            print_exact_error "Database Migrations Failed in plane-migrator (exit code ${MIGRATOR_EXIT})" "$MIGRATOR_LOGS"
            record_failure "STEP 5: Database Migrations" "${DOCKER_CMD} logs plane-migrator" "$MIGRATOR_EXIT" "$MIGRATOR_LOGS"
            SETUP_SUCCESS=false
        fi
        break
    fi
    sleep 2
done

if [ "$MIGRATOR_OK" = false ] && [ "$SETUP_SUCCESS" = true ]; then
    MIGRATOR_LOGS=$(${DOCKER_CMD} logs --tail 30 plane-migrator 2>&1 || echo "Could not retrieve migrator logs")
    print_item "warn" "Migrator still running after $((MIGRATOR_RETRIES * 2))s; check logs"
    print_exact_error "plane-migrator Did Not Complete Within Timeout ($((MIGRATOR_RETRIES * 2))s)" "$MIGRATOR_LOGS"
    record_failure "STEP 5: Database Migrations Timeout" "${DOCKER_CMD} inspect plane-migrator" 124 "$MIGRATOR_LOGS"
fi

# --- Phase 2: Wait for API to be healthy (not in restart loop) ---
APP_READY=false
HTTP_STATUS="000"
API_STATUS="000"

if [ "$MIGRATOR_OK" = true ]; then
    RETRIES=30
    WAIT_SECONDS=3
    for i in $(seq 1 $RETRIES); do
        API_RUNNING=$(${DOCKER_CMD} inspect --format='{{.State.Status}}' api 2>/dev/null || echo "missing")
        if [ "$API_RUNNING" = "running" ]; then
            HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://127.0.0.1:80/" 2>/dev/null || echo "000")
            API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://127.0.0.1:80/api/instances/" 2>/dev/null || echo "000")

            if [ "$HTTP_STATUS" = "200" ] && [ "$API_STATUS" = "200" ]; then
                APP_READY=true
                break
            fi
        fi
        sleep $WAIT_SECONDS
    done

    # --- Phase 3: Verify no critical containers are in restart loops ---
    RESTART_ISSUES=false
    for svc in api bgworker web proxy plane-db plane-redis; do
        SVC_STATUS=$(${DOCKER_CMD} inspect --format='{{.State.Status}}' "$svc" 2>/dev/null || echo "missing")
        SVC_RESTARTS=$(${DOCKER_CMD} inspect --format='{{.RestartCount}}' "$svc" 2>/dev/null || echo "0")
        if [ "$SVC_STATUS" = "restarting" ] || [ "$SVC_RESTARTS" -gt 2 ] 2>/dev/null; then
            SVC_LOGS=$(${DOCKER_CMD} logs --tail 35 "$svc" 2>&1 || echo "Could not retrieve logs for $svc")
            print_item "fail" "Service '${svc}' is crash-looping (restarts: ${SVC_RESTARTS}, status: ${SVC_STATUS})"
            print_exact_error "Service '${svc}' Crash-Loop Diagnostics" "$SVC_LOGS"
            record_failure "STEP 5: Container Stability (${svc})" "${DOCKER_CMD} logs ${svc}" 1 "$SVC_LOGS"
            RESTART_ISSUES=true
            SETUP_SUCCESS=false
        fi
    done

    if [ "$APP_READY" = true ] && [ "$RESTART_ISSUES" = false ]; then
        print_item "ok" "Frontend web gateway responding (HTTP 200)"
        print_item "ok" "Backend API and database operational (HTTP 200)"
        print_item "ok" "All core application components are healthy"
    elif [ "$RESTART_ISSUES" = true ]; then
        print_item "fail" "Critical backend services are failing — deployment is NOT healthy"
    else
        API_LOGS=$(${DOCKER_CMD} logs --tail 40 api 2>&1 || echo "Could not retrieve API logs")
        PROXY_LOGS=$(${DOCKER_CMD} logs --tail 25 proxy 2>&1 || echo "Could not retrieve Proxy logs")
        print_item "fail" "Backend API failed readiness check (Gateway: ${HTTP_STATUS}, API: ${API_STATUS})"
        print_exact_error "Readiness Check Failed (Gateway HTTP: ${HTTP_STATUS}, API HTTP: ${API_STATUS})" "--- Last 40 API Logs ---\n${API_LOGS}\n\n--- Last 25 Proxy Logs ---\n${PROXY_LOGS}"
        record_failure "STEP 5: Service Health Checks" "curl http://127.0.0.1:80/api/instances/" 1 "Gateway HTTP ${HTTP_STATUS}, API HTTP ${API_STATUS}\n${API_LOGS}"
        SETUP_SUCCESS=false
    fi
else
    print_item "warn" "Skipped API health checks due to migrator failure"
fi

print_step_done

# ==============================================================================
# Summary & Application Status Dashboard
# ==============================================================================
echo ""
if [ "$SETUP_SUCCESS" = true ]; then
    echo -e " ${CLR_SUCCESS}${CLR_BOLD}✓  one flow has been successfully deployed and started!${CLR_RESET}"
    echo -e " ${CLR_MUTED}All configuration files, containers, and services are up and running.${CLR_RESET}"
    echo ""

    DASH_W=74
    TITLE="APPLICATION STATUS: ONLINE"
    T_PREFIX="╭─[ ${TITLE} ]"
    T_PREFIX_LEN=${#T_PREFIX}
    DASH_COUNT=$(( DASH_W - T_PREFIX_LEN - 1 ))
    BOT_DASH=$(( DASH_W - 2 ))
    echo -e " ${CLR_PRIMARY}${T_PREFIX}$(printf "─%.0s" $(seq 1 $DASH_COUNT))╮${CLR_RESET}"
    box_row $DASH_W ""
    box_row $DASH_W "  ${CLR_SUCCESS}${CLR_BOLD}●${CLR_RESET}  ${CLR_BOLD}one flow services are fully deployed and operational!${CLR_RESET}"
    box_row $DASH_W ""
    box_row $DASH_W "  ${CLR_BOLD}Service Endpoints:${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Web App (Origin):${CLR_RESET}  ${CLR_PRIMARY}${FINAL_ORIGIN}${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Web App (Local):${CLR_RESET}   ${CLR_MUTED}http://localhost${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}God Mode (Admin):${CLR_RESET} ${CLR_MUTED}${FINAL_ORIGIN}/god-mode/${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Spaces (Public):${CLR_RESET}  ${CLR_MUTED}${FINAL_ORIGIN}/spaces/${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}REST API:${CLR_RESET}         ${CLR_MUTED}${FINAL_ORIGIN}/api/${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Live Collab:${CLR_RESET}      ${CLR_MUTED}${FINAL_ORIGIN}/live/ (WebSocket Engine)${CLR_RESET}"
    box_row $DASH_W ""
    box_row $DASH_W "  ${CLR_BOLD}Management Shortcuts:${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Live Logs:${CLR_RESET}  ${CLR_MUTED}${DOCKER_CMD} compose logs -f${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Restart:${CLR_RESET}    ${CLR_MUTED}${DOCKER_CMD} compose restart${CLR_RESET}"
    box_row $DASH_W "     ${CLR_TEXT}Stop:${CLR_RESET}       ${CLR_MUTED}${DOCKER_CMD} compose down${CLR_RESET}"
    box_row $DASH_W ""
    echo -e " ${CLR_PRIMARY}╰$(printf "─%.0s" $(seq 1 $BOT_DASH))╯${CLR_RESET}"
    echo ""
    echo -e " ${CLR_MUTED}Documentation & Support:${CLR_RESET} ${CLR_PRIMARY}https://github.com/sohan20051519/oneflow${CLR_RESET}"
    echo ""
    exit 0
else
    echo ""
    echo -e " ${CLR_DANGER}${CLR_BOLD}╭──────────────────────────────────────────────────────────────────────────╮${CLR_RESET}"
    echo -e " ${CLR_DANGER}${CLR_BOLD}│  DEPLOYMENT FAILED — EXACT ERROR DIAGNOSTICS                            │${CLR_RESET}"
    echo -e " ${CLR_DANGER}${CLR_BOLD}╰──────────────────────────────────────────────────────────────────────────╯${CLR_RESET}"
    echo ""
    
    if [ ${#FAIL_STEPS[@]} -gt 0 ]; then
        for ((idx=0; idx<${#FAIL_STEPS[@]}; idx++)); do
            echo -e " ${CLR_DANGER}${CLR_BOLD}● Failure $((idx+1)): ${FAIL_STEPS[$idx]}${CLR_RESET}"
            if [ -n "${FAIL_COMMANDS[$idx]}" ]; then
                echo -e "   ${CLR_MUTED}Command:${CLR_RESET}   ${CLR_TEXT}${FAIL_COMMANDS[$idx]}${CLR_RESET}"
            fi
            if [ -n "${FAIL_EXITCODES[$idx]}" ]; then
                echo -e "   ${CLR_MUTED}Exit Code:${CLR_RESET} ${CLR_DANGER}${FAIL_EXITCODES[$idx]}${CLR_RESET}"
            fi
            if [ -n "${FAIL_DETAILS[$idx]}" ]; then
                echo -e "   ${CLR_MUTED}Exact Output:${CLR_RESET}"
                while IFS= read -r f_line; do
                    echo -e "     ${CLR_DANGER}│${CLR_RESET} ${f_line}"
                done <<< "${FAIL_DETAILS[$idx]}"
            fi
            echo ""
        done
    else
        echo -e " ${CLR_DANGER}Deployment failed during health verification.${CLR_RESET}"
        echo -e " Please check: ${CLR_TEXT}${DOCKER_CMD} compose logs --tail 50${CLR_RESET}"
        echo ""
    fi

    echo -e " For assistance, visit: ${CLR_PRIMARY}https://github.com/sohan20051519/oneflow${CLR_RESET}"
    echo ""
    exit 1
fi
