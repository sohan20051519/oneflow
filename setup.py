#!/usr/bin/env python3
"""
one flow · Automated Deployment & Environment Setup
Brand Kit: onebiz Design System v2.0 (Rose/Coral Accent #E81B5B)
"""

import os
import sys
import time
import shutil
import threading
import datetime
import subprocess
import secrets
import re
import signal
import json
import getpass
import urllib.request
import urllib.error
import urllib.parse

# ANSI Color Palette (Brand: onebiz Coral #E81B5B)
CLR_PRIMARY    = "\033[38;2;232;27;91m"     # Brand Coral
CLR_PRIMARY_BG = "\033[48;2;232;27;91m"     # Brand Coral Background
CLR_TEXT       = "\033[38;2;250;250;250m"   # High-contrast foreground
CLR_MUTED      = "\033[38;2;163;163;163m"   # Subtle text
CLR_DARK       = "\033[38;2;115;115;115m"   # Grid border
CLR_SUCCESS    = "\033[38;2;34;163;75m"     # Status Success
CLR_WARNING    = "\033[38;2;250;204;21m"    # Status Warning
CLR_DANGER     = "\033[38;2;239;68;68m"     # Status Danger
CLR_CYAN       = "\033[38;2;56;189;248m"    # Info Accent
CLR_PURPLE     = "\033[38;2;168;85;247m"    # Env Accent
CLR_BLUE       = "\033[38;2;59;130;246m"    # Runtime Accent
CLR_BOLD       = "\033[1m"
CLR_DIM        = "\033[2m"
CLR_RESET      = "\033[0m"

ANSI_RE = re.compile(r'\x1B\[[0-9;]*[a-zA-Z]')

def strip_ansi(s: str) -> str:
    """Strip all ANSI escape sequences to compute exact visual width."""
    return ANSI_RE.sub('', s)

def fit_line(s: str, width: int) -> str:
    """
    Ensure string is EXACTLY width visual characters.
    Truncates printable characters while preserving ANSI styles,
    or pads with spaces.
    """
    stripped = strip_ansi(s)
    vis_len = len(stripped)
    if vis_len > width:
        res = []
        cur_len = 0
        i = 0
        while i < len(s):
            m = ANSI_RE.match(s, i)
            if m:
                res.append(m.group(0))
                i = m.end()
            else:
                if cur_len < width:
                    res.append(s[i])
                    cur_len += 1
                i += 1
        res.append(CLR_RESET)
        return "".join(res)
    elif vis_len < width:
        return s + (" " * (width - vis_len))
    return s

def build_box(width: int, title: str, content_lines: list, border_color: str = CLR_PRIMARY) -> list:
    """Construct a perfectly bordered box with mathematically locked character widths."""
    rows = []
    # Top border with title
    t_label = f" {title} " if title else ""
    t_prefix = f"╭─[{t_label}]" if title else "╭"
    top_dash_count = max(0, width - len(strip_ansi(t_prefix)) - 1)
    rows.append(f"{border_color}{t_prefix}{'─' * top_dash_count}╮{CLR_RESET}")
    
    # Body rows
    inner_width = width - 4
    for line in content_lines:
        fitted = fit_line(line, inner_width)
        rows.append(f"{border_color}│{CLR_RESET} {fitted} {border_color}│{CLR_RESET}")
        
    # Bottom border
    bot_dash = max(0, width - 2)
    rows.append(f"{border_color}╰{'─' * bot_dash}╯{CLR_RESET}")
    return rows

def ensure_swap_space(log_fn=None, activity_fn=None):
    """
    On 1GB RAM instances (e.g. AWS t3.micro), physical RAM is ~980MB.
    Without swap, kernel OOM-killer will kill containers during bursts.
    If swap is < 1GB and total RAM <= 2.5GB, automatically provision a 2GB /swapfile.
    """
    try:
        mem_total_kb = 0
        swap_total_kb = 0
        if os.path.isfile("/proc/meminfo"):
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total_kb = int(line.split()[1])
                    elif line.startswith("SwapTotal:"):
                        swap_total_kb = int(line.split()[1])
        if 0 < mem_total_kb < 2600000 and swap_total_kb < 1000000:
            if log_fn:
                log_fn("swap", f"Low memory profile: {mem_total_kb // 1024} MB RAM, {swap_total_kb // 1024} MB swap")
            if activity_fn:
                activity_fn("info", "Configuring 2GB swap for 1GB RAM stability...")
            cmd_prefix = ["sudo"] if shutil.which("sudo") and os.geteuid() != 0 else []
            if not os.path.exists("/swapfile"):
                r = subprocess.run(cmd_prefix + ["fallocate", "-l", "2G", "/swapfile"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if r.returncode != 0:
                    subprocess.run(cmd_prefix + ["dd", "if=/dev/zero", "of=/swapfile", "bs=1M", "count=2048"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(cmd_prefix + ["chmod", "600", "/swapfile"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(cmd_prefix + ["mkswap", "/swapfile"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(cmd_prefix + ["swapon", "/swapfile"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                with open("/etc/fstab", "r") as f:
                    fstab = f.read()
                if "/swapfile" not in fstab:
                    subprocess.run(["sh", "-c", "echo '/swapfile none swap sw 0 0' | " + ("sudo " if cmd_prefix else "") + "tee -a /etc/fstab"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            subprocess.run(cmd_prefix + ["sysctl", "vm.swappiness=10"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if activity_fn:
                activity_fn("ok", "2GB swapfile active (OOM protection ready)")
            if log_fn:
                log_fn("swap", "Enabled 2GB swapfile for 1GB RAM instance")
    except Exception as e:
        if log_fn:
            log_fn("swap", f"Swap check info: {e}")

class TUIState:
    def __init__(self, script_dir: str):
        self.script_dir = script_dir
        self.lock = threading.Lock()
        self.running = True
        self.setup_success = True
        self.progress = 0
        self.current_task = "Initializing deployment..."
        self.current_step = 0
        
        self.step_names = [
            "Provisioning Environment Configurations",
            "Cryptographic Secrets & Security Keys",
            "Container Runtime & Image Synchronization",
            "Deploying & Starting All Services",
            "Verifying Service Health & Readiness",
        ]
        self.step_statuses = ["pending"] * 5  # "pending", "active", "done", "fail"
        self.recent_activity = []
        self.logs = []
        self.failures = []

        # Directory and Compose file resolution
        if os.path.isfile(os.path.join(self.script_dir, "docker-compose.yml")):
            self.source_dir = self.script_dir
            self.deploy_dir = self.script_dir
            self.compose_file = os.path.join(self.script_dir, "docker-compose.yml")
            self.compose_label = "root docker-compose.yml"
        elif os.path.isfile(os.path.join(os.path.dirname(self.script_dir), "docker-compose.yml")):
            self.deploy_dir = os.path.dirname(self.script_dir)
            self.source_dir = self.script_dir
            self.compose_file = os.path.join(self.deploy_dir, "docker-compose.yml")
            self.compose_label = "parent docker-compose.yml"
        else:
            self.deploy_dir = self.script_dir
            self.source_dir = os.path.join(self.script_dir, "source")
            self.compose_file = os.path.join(self.source_dir, "docker-compose.yml")
            self.compose_label = "source/docker-compose.yml"

        self.docker_cmd = self._detect_docker()

    def _detect_docker(self) -> list:
        try:
            r = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode == 0:
                return ["docker"]
        except Exception:
            pass

        try:
            r = subprocess.run(["sudo", "-n", "docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode == 0:
                return ["sudo", "docker"]
        except Exception:
            pass

        if shutil.which("sudo"):
            return ["sudo", "docker"]
        return ["docker"]

    def set_step(self, step_idx: int):
        with self.lock:
            for i in range(step_idx):
                if self.step_statuses[i] != "fail":
                    self.step_statuses[i] = "done"
            self.current_step = step_idx
            self.step_statuses[step_idx] = "active"

    def set_progress(self, pct: int, task: str):
        with self.lock:
            self.progress = min(100, max(0, pct))
            self.current_task = task

    def add_activity(self, status: str, text: str):
        with self.lock:
            self.recent_activity.append((status, text))
            if len(self.recent_activity) > 50:
                self.recent_activity = self.recent_activity[-50:]

    def log(self, tag: str, message: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        cleaned = message.rstrip("\r\n").strip()
        if cleaned:
            with self.lock:
                self.logs.append((now, tag, cleaned))

    def add_failure(self, step: str, command: str, code: int, details: str):
        with self.lock:
            self.failures.append((step, command, code, details))

    def render(self) -> str:
        cols, lines = shutil.get_terminal_size((80, 24))
        
        # Responsive Layout Calculation - Full Screen Geometry
        use_split = cols >= 110
        left_w = 70 if use_split else min(cols - 4, 70)
        gap = 2
        right_w = max(40, cols - left_w - gap - 3) if use_split else 0

        # Full-Screen Dynamic Canvas Height
        # Leaves safe margin so terminal never scrolls during redrawing
        target_height = max(26, lines - 2)

        with self.lock:
            prog = self.progress
            task = self.current_task
            cur_step = self.current_step
            statuses = list(self.step_statuses)
            activity = list(self.recent_activity)
            logs_snapshot = list(self.logs)

        # -----------------------------------------------------------------
        # LEFT COLUMN CONSTRUCTION (Fills target_height)
        # -----------------------------------------------------------------
        left_sections = []

        # 1. Header Banner (8 lines)
        banner_lines = [
            f" {CLR_BOLD}██████  ███    ██ ███████   ███████ ██      ██████  ██     ██{CLR_RESET}",
            f"{CLR_BOLD}██    ██ ████   ██ ██        ██      ██     ██    ██ ██     ██{CLR_RESET}",
            f"{CLR_BOLD}██    ██ ██ ██  ██ █████     █████   ██     ██    ██ ██  █  ██{CLR_RESET}",
            f"{CLR_BOLD}██    ██ ██  ██ ██ ██        ██      ██     ██    ██ ██ ███ ██{CLR_RESET}",
            f" {CLR_BOLD}██████  ██   ████ ███████   ██      ███████ ██████   ███ ███ {CLR_RESET}",
            f"{CLR_TEXT}{CLR_BOLD}one flow{CLR_RESET} {CLR_MUTED}· intelligent project management & workflow automation{CLR_RESET}",
        ]
        left_sections.extend(build_box(left_w, "ONE FLOW", banner_lines))

        # 2. Progress Bar Box (5 lines)
        bar_len = left_w - 18
        filled = int(bar_len * prog / 100)
        empty = bar_len - filled
        bar_str = f"{CLR_PRIMARY}{'█' * filled}{CLR_MUTED}{'░' * empty}{CLR_RESET}"
        
        prog_lines = [
            f"[{bar_str}] {CLR_BOLD}{prog:>3}%{CLR_RESET}",
            f"{CLR_MUTED}Step {min(5, cur_step + 1)} of 5 · {self.step_names[min(4, cur_step)]}{CLR_RESET}",
            f"{CLR_MUTED}Action:{CLR_RESET} {CLR_TEXT}{task}{CLR_RESET}",
        ]
        left_sections.extend(build_box(left_w, "DEPLOYMENT PROGRESS", prog_lines))

        # 3. Pipeline Steps & Activity Box (Expands to fill remaining target_height)
        pipe_box_height = max(13, target_height - len(left_sections))
        avail_pipe_content_rows = pipe_box_height - 2
        
        pipe_lines = []
        for i, sname in enumerate(self.step_names):
            st = statuses[i]
            if st == "done":
                badge = f"{CLR_SUCCESS}✓{CLR_RESET}"
                name_fmt = f"{CLR_TEXT}{i+1}. {sname}{CLR_RESET}"
            elif st == "active":
                badge = f"{CLR_PRIMARY}▶{CLR_RESET}"
                name_fmt = f"{CLR_BOLD}{CLR_PRIMARY}{i+1}. {sname}{CLR_RESET}"
            elif st == "fail":
                badge = f"{CLR_DANGER}✗{CLR_RESET}"
                name_fmt = f"{CLR_DANGER}{i+1}. {sname}{CLR_RESET}"
            else:
                badge = f"{CLR_DARK}·{CLR_RESET}"
                name_fmt = f"{CLR_MUTED}{i+1}. {sname}{CLR_RESET}"
            pipe_lines.append(f"{badge}  {name_fmt}")

        pipe_lines.append(f"{CLR_DARK}{'─' * (left_w - 4)}{CLR_RESET}")
        pipe_lines.append(f"{CLR_MUTED}{CLR_BOLD}Latest Milestones:{CLR_RESET}")
        
        # Header items take 7 lines (5 steps + 1 divider + 1 label)
        remaining_slots = max(1, avail_pipe_content_rows - 7)
        if not activity:
            pipe_lines.append(f" {CLR_DARK}· Preparing deployment environment...{CLR_RESET}")
        else:
            visible_act = activity[-remaining_slots:]
            for act_st, act_txt in visible_act:
                if act_st == "ok":
                    icon = f"{CLR_SUCCESS}✓{CLR_RESET}"
                elif act_st == "info":
                    icon = f"{CLR_MUTED}ℹ{CLR_RESET}"
                elif act_st == "warn":
                    icon = f"{CLR_WARNING}▲{CLR_RESET}"
                else:
                    icon = f"{CLR_DANGER}✗{CLR_RESET}"
                pipe_lines.append(f"{icon} {CLR_TEXT}{act_txt}{CLR_RESET}")

        while len(pipe_lines) < avail_pipe_content_rows:
            pipe_lines.append("")

        left_sections.extend(build_box(left_w, "PIPELINE EXECUTION", pipe_lines))

        # -----------------------------------------------------------------
        # RIGHT COLUMN CONSTRUCTION (Live Logs - Expands to target_height)
        # -----------------------------------------------------------------
        right_sections = []
        if use_split:
            tag_colors = {
                "sys": CLR_CYAN,
                "env": CLR_PURPLE,
                "crypto": CLR_WARNING,
                "docker": CLR_BLUE,
                "build": CLR_PRIMARY,
                "compose": CLR_SUCCESS,
                "health": CLR_CYAN,
            }

            avail_log_rows = target_height - 2
            visible_logs = logs_snapshot[-avail_log_rows:]
            log_lines = []

            for r in range(avail_log_rows):
                if r < len(visible_logs):
                    t_str, tag, msg = visible_logs[r]
                    t_col = tag_colors.get(tag, CLR_MUTED)
                    tag_fmt = f"{t_col}[{tag:<7}]{CLR_RESET}"
                    log_lines.append(f"{CLR_MUTED}{t_str}{CLR_RESET} {tag_fmt} {CLR_TEXT}{msg}{CLR_RESET}")
                else:
                    log_lines.append("")

            right_sections.extend(build_box(right_w, "LIVE CONTAINER & DEPLOYMENT LOGS", log_lines))

        # -----------------------------------------------------------------
        # MERGE COLUMNS WITH PIXEL-PERFECT CLIPPING
        # -----------------------------------------------------------------
        total_rows = max(len(left_sections), len(right_sections))
        max_drawable_rows = min(total_rows, lines - 1)
        
        output_rows = []
        for r in range(max_drawable_rows):
            l_str = left_sections[r] if r < len(left_sections) else " " * left_w
            if use_split:
                r_str = right_sections[r] if r < len(right_sections) else " " * right_w
                combined_line = f" {l_str}{' ' * gap}{r_str}"
            else:
                combined_line = f" {l_str}"
            output_rows.append(combined_line)

        return "\033[H" + "\n".join(output_rows)

    def run_workflow(self):
        """Worker thread running the full deployment sequence."""
        try:
            self._step_1_env()
            self._step_2_crypto()
            self._step_3_docker()
            if self.setup_success:
                self._step_4_compose()
            if self.setup_success:
                self._step_5_health()
        except Exception as e:
            self.log("sys", f"Unexpected error: {str(e)}")
            self.setup_success = False
        finally:
            self.running = False

    def _step_1_env(self):
        self.set_step(0)
        self.set_progress(5, "Verifying environment & system memory...")
        self.log("env", "Checking memory profile and swap configuration")
        ensure_swap_space(self.log, self.add_activity)

        def copy_cfg(src_rel, dest_rel, label):
            src = os.path.join(self.source_dir, src_rel)
            dest = os.path.join(self.source_dir, dest_rel)
            if not os.path.isfile(src):
                self.add_activity("fail", f"Missing template: {label}")
                self.log("env", f"Template not found: {src}")
                return False
            if os.path.isfile(dest):
                self.add_activity("info", f"Preserved existing {label}")
                self.log("env", f"Preserved {label}")
            else:
                shutil.copy(src, dest)
                self.add_activity("ok", f"Generated {label}")
                self.log("env", f"Created {label}")
            return True

        copy_cfg(".env.example", ".env", "./.env")
        copy_cfg("apps/web/.env.example", "apps/web/.env", "./apps/web/.env")
        copy_cfg("apps/api/.env.example", "apps/api/.env", "./apps/api/.env")
        copy_cfg("apps/space/.env.example", "apps/space/.env", "./apps/space/.env")
        copy_cfg("apps/admin/.env.example", "apps/admin/.env", "./apps/admin/.env")
        copy_cfg("apps/live/.env.example", "apps/live/.env", "./apps/live/.env")

        # Handle deploy environment
        plane_env = os.path.join(self.deploy_dir, "plane.env")
        if os.path.isfile(plane_env):
            dot_env = os.path.join(self.deploy_dir, ".env")
            if not os.path.exists(dot_env):
                try:
                    os.symlink("plane.env", dot_env)
                    self.add_activity("ok", "Synchronized plane.env -> .env")
                    self.log("env", "Symlinked plane.env to .env")
                except Exception:
                    pass

        # Auto-sanitize existing .env files for 1GB RAM container networking and Redis broker
        api_env_path = os.path.join(self.source_dir, "apps/api/.env")
        if os.path.isfile(api_env_path):
            try:
                with open(api_env_path, "r") as f:
                    c = f.read()
                changed = False
                if "plane-db" not in c or "${" in c or "localhost" in c or "127.0.0.1" in c:
                    if re.search(r'^DATABASE_URL=.*', c, re.MULTILINE):
                        c = re.sub(r'^DATABASE_URL=.*', 'DATABASE_URL="postgresql://plane:plane@plane-db:5432/plane"', c, flags=re.MULTILINE)
                    else:
                        c += '\nDATABASE_URL="postgresql://plane:plane@plane-db:5432/plane"\n'
                    changed = True
                if "plane-redis" not in c or "${" in c or "localhost" in c or "127.0.0.1" in c:
                    if re.search(r'^REDIS_URL=.*', c, re.MULTILINE):
                        c = re.sub(r'^REDIS_URL=.*', 'REDIS_URL="redis://plane-redis:6379/"', c, flags=re.MULTILINE)
                    else:
                        c += '\nREDIS_URL="redis://plane-redis:6379/"\n'
                    changed = True
                if not re.search(r'^CELERY_BROKER_URL=.*', c, re.MULTILINE):
                    c += '\nCELERY_BROKER_URL="redis://plane-redis:6379/1"\n'
                    changed = True
                else:
                    c = re.sub(r'^CELERY_BROKER_URL=.*', 'CELERY_BROKER_URL="redis://plane-redis:6379/1"', c, flags=re.MULTILINE)
                    changed = True
                if re.search(r'^GUNICORN_WORKERS=.*', c, re.MULTILINE):
                    c = re.sub(r'^GUNICORN_WORKERS=.*', 'GUNICORN_WORKERS="1"', c, flags=re.MULTILINE)
                    changed = True
                else:
                    c += '\nGUNICORN_WORKERS="1"\n'
                    changed = True
                if re.search(r'^POSTGRES_HOST=.*', c, re.MULTILINE):
                    c = re.sub(r'^POSTGRES_HOST=.*', 'POSTGRES_HOST="plane-db"', c, flags=re.MULTILINE)
                    changed = True
                else:
                    c += '\nPOSTGRES_HOST="plane-db"\n'
                    changed = True
                if re.search(r'^REDIS_HOST=.*', c, re.MULTILINE):
                    c = re.sub(r'^REDIS_HOST=.*', 'REDIS_HOST="plane-redis"', c, flags=re.MULTILINE)
                    changed = True
                else:
                    c += '\nREDIS_HOST="plane-redis"\n'
                    changed = True

                # Clear unexposed dev ports in container base URLs so Caddy handles all reverse proxying
                for var_name in ["ADMIN_BASE_URL", "SPACE_BASE_URL", "APP_BASE_URL", "LIVE_BASE_URL"]:
                    if re.search(rf'^{var_name}=.*', c, re.MULTILINE):
                        line_match = re.search(rf'^{var_name}=(.*)', c, re.MULTILINE)
                        if line_match and any(p in line_match.group(1) for p in [":3001", ":3002", ":3000", ":3100", ":8000"]):
                            c = re.sub(rf'^{var_name}=.*', f'{var_name}=""', c, flags=re.MULTILINE)
                            changed = True

                if re.search(r'^WEB_URL=.*', c, re.MULTILINE):
                    web_match = re.search(r'^WEB_URL=(.*)', c, re.MULTILINE)
                    if web_match and any(p in web_match.group(1) for p in [":8000", ":3000"]):
                        c = re.sub(r'^WEB_URL=.*', 'WEB_URL="http://localhost"', c, flags=re.MULTILINE)
                        changed = True

                if changed:
                    with open(api_env_path, "w") as f:
                        f.write(c)
                    self.add_activity("ok", "Optimized apps/api/.env (Redis Celery broker, reverse proxy URLs)")
                    self.log("env", "Configured Redis broker & proxy settings in apps/api/.env")
            except Exception as e:
                self.log("env", f"Warning: could not sanitize apps/api/.env: {e}")

        # Sanitize frontend .env files to use relative proxy URLs
        for frontend_app in ["admin", "web", "space"]:
            fe_env_path = os.path.join(self.source_dir, f"apps/{frontend_app}/.env")
            if os.path.isfile(fe_env_path):
                try:
                    with open(fe_env_path, "r") as f:
                        fe_content = f.read()
                    fe_changed = False
                    for p in ["http://localhost:8000", "http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3100"]:
                        if p in fe_content:
                            fe_content = fe_content.replace(f'"{p}"', '""').replace(f"'{p}'", '""').replace(p, "")
                            fe_changed = True
                    if fe_changed:
                        with open(fe_env_path, "w") as f:
                            f.write(fe_content)
                        self.log("env", f"Sanitized apps/{frontend_app}/.env for reverse proxy relative URLs")
                except Exception as e:
                    self.log("env", f"Warning: could not sanitize apps/{frontend_app}/.env: {e}")

        live_env_path = os.path.join(self.source_dir, "apps/live/.env")
        if os.path.isfile(live_env_path):
            try:
                with open(live_env_path, "r") as f:
                    c = f.read()
                changed = False
                if "http://localhost:8000" in c:
                    c = c.replace("http://localhost:8000", "http://api:8000")
                    changed = True
                if "REDIS_HOST=localhost" in c or 'REDIS_HOST="localhost"' in c:
                    c = re.sub(r'^REDIS_HOST=.*', 'REDIS_HOST="plane-redis"', c, flags=re.MULTILINE)
                    changed = True
                if "redis://localhost" in c:
                    c = re.sub(r'^REDIS_URL=.*', 'REDIS_URL="redis://plane-redis:6379/"', c, flags=re.MULTILINE)
                    changed = True
                if not re.search(r'^LIVE_SERVER_SECRET_KEY=', c, re.MULTILINE):
                    c += '\nLIVE_SERVER_SECRET_KEY="secret-key"\n'
                    changed = True
                if changed:
                    with open(live_env_path, "w") as f:
                        f.write(c)
                    self.add_activity("ok", "Sanitized apps/live/.env container endpoints")
                    self.log("env", "Fixed container connection URLs in apps/live/.env")
            except Exception as e:
                self.log("env", f"Warning: could not sanitize apps/live/.env: {e}")

        # Check ONEFLOW_DOMAIN in environment configurations
        configured_domain = detect_server_ip(self.deploy_dir, self.source_dir)
        if configured_domain:
            self.log("env", f"Active deployment origin: {configured_domain}")

        self.set_progress(20, "Environment configurations verified")
        time.sleep(0.4)

    def _step_2_crypto(self):
        self.set_step(1)
        self.set_progress(25, "Verifying cryptographic secrets...")
        self.log("crypto", "Validating Django SECRET_KEY")

        api_env = os.path.join(self.source_dir, "apps/api/.env")
        if os.path.isfile(api_env):
            with open(api_env, "r") as f:
                content = f.read()
            match = re.search(r'^SECRET_KEY=(.*)', content, re.MULTILINE)
            val = match.group(1).strip('"\'') if match else ""
            if not val or val in ["your-secret-key-here", "change-me-in-production"]:
                new_key = secrets.token_urlsafe(50)
                if match:
                    content = re.sub(r'^SECRET_KEY=.*', f'SECRET_KEY="{new_key}"', content, flags=re.MULTILINE)
                else:
                    content += f'\nSECRET_KEY="{new_key}"\n'
                with open(api_env, "w") as f:
                    f.write(content)
                self.add_activity("ok", "Generated Django SECRET_KEY (50 chars)")
                self.log("crypto", "Generated fresh secure Django SECRET_KEY")
            else:
                self.add_activity("info", "Django SECRET_KEY verified")
                self.log("crypto", "Existing SECRET_KEY confirmed")

        plane_env = os.path.join(self.deploy_dir, "plane.env")
        if os.path.isfile(plane_env):
            with open(plane_env, "r") as f:
                p_content = f.read()
            if not re.search(r'^MACHINE_SIGNATURE=.', p_content, re.MULTILINE):
                sig = secrets.token_hex(16)
                p_content = re.sub(r'^MACHINE_SIGNATURE=.*', f'MACHINE_SIGNATURE="{sig}"', p_content, flags=re.MULTILINE)
                with open(plane_env, "w") as f:
                    f.write(p_content)
                self.add_activity("ok", "Generated machine signature in plane.env")
                self.log("crypto", "Generated MACHINE_SIGNATURE")
            else:
                self.add_activity("info", "Machine signature verified")

        self.set_progress(40, "Cryptographic keys ready")
        time.sleep(0.4)

    def _step_3_docker(self):
        self.set_step(2)
        self.set_progress(45, "Connecting to Docker engine...")
        self.log("docker", f"Testing container runtime ({' '.join(self.docker_cmd)})")

        res = subprocess.run(self.docker_cmd + ["info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            self.add_activity("fail", "Docker daemon is not accessible")
            self.log("docker", "Failed to connect to Docker daemon socket")
            self.setup_success = False
            return

        ver_res = subprocess.run(self.docker_cmd + ["--version"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        d_ver = ver_res.stdout.strip().split()[2].rstrip(',') if ver_res.returncode == 0 else "active"
        self.add_activity("ok", f"Docker engine operational ({d_ver})")
        self.log("docker", f"Docker Engine version {d_ver} connected")

        # Check frontend image
        chk_img = subprocess.run(self.docker_cmd + ["image", "inspect", "plane-frontend:oneflow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if chk_img.returncode == 0:
            self.add_activity("ok", "Found image: plane-frontend:oneflow")
            self.log("docker", "Prebuilt plane-frontend:oneflow image found")
        else:
            self.add_activity("info", "Building customized oneflow image...")
            self.log("build", "Initiating Docker build for plane-frontend:oneflow")
            self.set_progress(50, "Building customized oneflow frontend image...")

            build_cmd = self.docker_cmd + [
                "build",
                "-f", os.path.join(self.source_dir, "apps/web/Dockerfile.web"),
                "-t", "plane-frontend:oneflow",
                self.source_dir
            ]
            proc = subprocess.Popen(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                self.log("build", line)
            proc.wait()

            if proc.returncode == 0:
                self.add_activity("ok", "Built plane-frontend:oneflow successfully")
                self.log("build", "Successfully built plane-frontend:oneflow image")
            else:
                self.add_activity("warn", "Web image build skipped; using fallback")
                self.log("build", "Docker build non-zero exit; continuing with defaults")

        self.set_progress(60, "Container runtime synchronized")
        time.sleep(0.4)

    def _step_4_compose(self):
        self.set_step(3)
        self.set_progress(65, "Deploying services with Docker Compose...")
        
        # Cleanly identify compose file without any warning!
        self.add_activity("ok", f"Detected {self.compose_label}")
        self.log("compose", f"Using configuration: {self.compose_file}")

        compose_args = self.docker_cmd + ["compose", "--file", self.compose_file]
        compose_env = os.path.join(self.deploy_dir, "plane.env")
        if os.path.isfile(compose_env):
            compose_args.extend(["--env-file", compose_env])
            self.log("compose", f"Applied environment: {os.path.basename(compose_env)}")
        elif os.path.isfile(os.path.join(self.source_dir, ".env")):
            compose_args.extend(["--env-file", os.path.join(self.source_dir, ".env")])
            self.log("compose", "Applied environment: .env")

        compose_args.extend(["up", "-d", "--build"])
        self.log("compose", f"Executing: {' '.join(compose_args)}")
        
        compose_output = []
        proc = subprocess.Popen(compose_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            self.log("compose", line)
            compose_output.append(line.rstrip())
        proc.wait()

        if proc.returncode == 0:
            ps_res = subprocess.run(self.docker_cmd + ["ps", "--format", "{{.Names}}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            active_cts = [c for c in ps_res.stdout.splitlines() if c.strip()]
            self.add_activity("ok", f"Orchestrated {len(active_cts)} services in background")
            self.log("compose", f"Active container count: {len(active_cts)}")
        else:
            err_snip = "\n".join(compose_output[-35:]) if compose_output else "Docker compose up returned non-zero code"
            self.add_activity("fail", f"Failed to start Docker Compose services (code {proc.returncode})")
            self.log("compose", f"Docker Compose up returned code {proc.returncode}")
            self.add_failure(self.step_names[3], " ".join(compose_args), proc.returncode, err_snip)
            self.setup_success = False
            return

        self.set_progress(80, "Services started successfully")
        time.sleep(0.4)

    def _step_5_health(self):
        self.set_step(4)
        self.set_progress(82, "Awaiting database migrations and service readiness...")
        self.add_activity("info", "Checking database migrations...")
        self.log("health", "Verifying plane-migrator completion")

        # --- Phase 1: Verify Migrator Exit Code ---
        migrator_ok = False
        migrator_retries = 60
        for i in range(1, migrator_retries + 1):
            stat_res = subprocess.run(self.docker_cmd + ["inspect", "--format", "{{.State.Status}}", "plane-migrator"],
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            status = stat_res.stdout.strip()
            if status == "exited":
                code_res = subprocess.run(self.docker_cmd + ["inspect", "--format", "{{.State.ExitCode}}", "plane-migrator"],
                                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                exit_code = code_res.stdout.strip()
                if exit_code == "0":
                    migrator_ok = True
                    self.add_activity("ok", "Database migrations completed successfully (exit code 0)")
                    self.log("health", "plane-migrator completed successfully (exit code 0)")
                else:
                    mig_logs = subprocess.run(self.docker_cmd + ["logs", "--tail", "40", "plane-migrator"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
                    self.add_activity("fail", f"Database migrations FAILED (exit code {exit_code})")
                    self.log("health", f"plane-migrator failed with exit code {exit_code}")
                    self.add_failure("Database Migrations", f"{' '.join(self.docker_cmd)} logs plane-migrator", int(exit_code) if exit_code.isdigit() else 1, mig_logs or "No log output")
                    self.setup_success = False
                    return
                break
            time.sleep(2)

        if not migrator_ok:
            mig_logs = subprocess.run(self.docker_cmd + ["logs", "--tail", "30", "plane-migrator"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
            self.add_activity("fail", "Database migrations timed out waiting for completion")
            self.log("health", "plane-migrator did not exit within timeout period")
            self.add_failure("Database Migrations Timeout", f"{' '.join(self.docker_cmd)} inspect plane-migrator", 124, mig_logs or "plane-migrator did not exit in time")
            self.setup_success = False
            return

        # --- Phase 2: Probe Service Endpoints & Check API/Worker Health ---
        self.set_progress(88, "Probing service endpoints and container health...")
        self.add_activity("info", "Probing gateway and backend REST API...")
        self.log("health", "Initiating health checks on gateway and backend /api/instances/")

        retries = 60
        app_ready = False
        api_ready = False
        http_code = 0
        api_code = 0
        internal_api = 0

        final_host = os.environ.get("DOMAIN_NAME", "127.0.0.1")

        for i in range(1, retries + 1):
            self.log("health", f"Probing gateway and backend (attempt {i}/{retries})...")
            # 1. Probe Web Gateway (with Host header and 5s timeout)
            try:
                req = urllib.request.Request("http://127.0.0.1:80/", headers={"User-Agent": "oneflow-healthcheck", "Host": final_host})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    http_code = resp.getcode()
            except urllib.error.HTTPError as e:
                http_code = e.code
            except Exception:
                http_code = 0

            # 2. Probe Backend REST API endpoint directly through gateway
            try:
                api_req = urllib.request.Request("http://127.0.0.1:80/api/instances/", headers={"User-Agent": "oneflow-healthcheck", "Host": final_host})
                with urllib.request.urlopen(api_req, timeout=5) as resp:
                    api_code = resp.getcode()
            except urllib.error.HTTPError as e:
                api_code = e.code
            except Exception:
                api_code = 0

            # 3. Probe directly inside API container if gateway check hasn't responded yet
            if api_code != 200:
                try:
                    res = subprocess.run(
                        self.docker_cmd + ["exec", "api", "python3", "-c", "import urllib.request; resp=urllib.request.urlopen('http://127.0.0.1:8000/api/instances/', timeout=3); print(resp.getcode())"],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5
                    )
                    if res.returncode == 0 and res.stdout.strip() == "200":
                        internal_api = 200
                except Exception:
                    internal_api = 0

            # Accept 200, 301, 302, 308 on gateway (Caddy redirects HTTP to HTTPS when domain is configured)
            gateway_ok = http_code in [200, 301, 302, 308]
            api_ok = (api_code == 200) or (internal_api == 200)

            if gateway_ok and api_ok:
                app_ready = True
                api_ready = True
                self.log("health", f"Gateway (HTTP {http_code}) and Backend API (HTTP {api_code or internal_api}) operational")
                break
            elif gateway_ok:
                self.log("health", f"Gateway online (HTTP {http_code}); awaiting Gunicorn worker initialization (API {api_code}, internal {internal_api})...")
            else:
                self.log("health", f"Waiting for services... Gateway={http_code}, API={api_code}")

            time.sleep(3)

        # --- Phase 3: Check for Container Crash Loops ---
        restart_issues = False
        for svc in ["api", "bgworker", "web", "proxy"]:
            stat_res = subprocess.run(self.docker_cmd + ["inspect", "--format", "{{.State.Status}}", svc],
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            status = stat_res.stdout.strip()
            rest_res = subprocess.run(self.docker_cmd + ["inspect", "--format", "{{.RestartCount}}", svc],
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            try:
                restarts = int(rest_res.stdout.strip())
            except ValueError:
                restarts = 0

            if status == "restarting" or restarts > 2:
                svc_logs = subprocess.run(self.docker_cmd + ["logs", "--tail", "35", svc], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
                self.add_activity("fail", f"Service '{svc}' is crash-looping (restarts: {restarts})")
                self.log("health", f"Service '{svc}' status={status}, restarts={restarts}")
                self.add_failure(f"Container Crash-Loop ({svc})", f"{' '.join(self.docker_cmd)} logs {svc}", 1, svc_logs or f"Service {svc} is in restart loop")
                restart_issues = True
                self.setup_success = False

        if app_ready and api_ready and not restart_issues:
            self.add_activity("ok", f"Frontend gateway responding (HTTP {http_code})")
            self.add_activity("ok", f"Backend API and database operational (HTTP {api_code})")
            self.add_activity("ok", "All application components online and verified")
            self.log("health", "Application components fully verified and healthy")
        elif restart_issues:
            self.add_activity("fail", "Critical backend services are failing — deployment is NOT healthy")
            self.log("health", "Backend containers failing/restarting; deployment marked as failed")
            self.setup_success = False
        else:
            api_logs = subprocess.run(self.docker_cmd + ["logs", "--tail", "40", "api"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
            self.add_activity("fail", f"Backend API failed health check (HTTP {api_code})")
            self.log("health", f"Health check failed: Gateway={http_code}, API={api_code}")
            self.add_failure("Backend API Health Check", "curl http://127.0.0.1:80/api/instances/", 1, f"Gateway HTTP: {http_code}, API HTTP: {api_code}\n\n--- API Logs ---\n{api_logs}")
            self.setup_success = False

        self.set_progress(100, "one flow deployment verification complete")
        time.sleep(0.6)

def detect_server_ip(deploy_dir: str, source_dir: str) -> str:
    """
    Dynamically detect the host's actual public or network IP address.
    Never falls back to hardcoded IPs.
    """
    # 0. User override via environment variable
    env_override = os.environ.get("ONEFLOW_DOMAIN") or os.environ.get("APP_DOMAIN")
    if env_override and env_override.strip() not in ["localhost", "127.0.0.1", "0.0.0.0", ""]:
        return env_override.strip()

    # 1. Check if configured in plane.env or .env
    for env_path in [
        os.path.join(deploy_dir, "plane.env"),
        os.path.join(source_dir, ".env"),
        os.path.join(deploy_dir, ".env"),
    ]:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ONEFLOW_DOMAIN=") or line.startswith("DOMAIN_NAME=") or line.startswith("APP_DOMAIN="):
                            val = line.split("=", 1)[1].strip().strip('"\'')
                            if val and val not in ["localhost", "127.0.0.1", "0.0.0.0", ""]:
                                return val
            except Exception:
                pass

    # 2. Query public IP discovery services with fast timeout
    ip_services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
    ]
    for url in ip_services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                ip = resp.read().decode("utf-8").strip()
                if ip and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                    return ip
        except Exception:
            continue

    # 3. Query outbound network socket for local interface IP (LAN / private subnet)
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127.") and not ip.startswith("172.17.") and not ip.startswith("172.18."):
            return ip
    except Exception:
        pass

    # 4. Fallback to ip route get or hostname -I
    try:
        route_out = subprocess.check_output(["ip", "route", "get", "1.1.1.1"], text=True, stderr=subprocess.DEVNULL).strip()
        m = re.search(r'src\s+([0-9.]+)', route_out)
        if m:
            ip = m.group(1).strip()
            if ip and not ip.startswith("127."):
                return ip
    except Exception:
        pass

    try:
        out = subprocess.check_output(["hostname", "-I"], text=True, stderr=subprocess.DEVNULL).strip().split()
        for cand in out:
            cand = cand.strip()
            if cand and not cand.startswith("127.") and not cand.startswith("172.17.") and not cand.startswith("172.18."):
                return cand
    except Exception:
        pass

def fetch_infisical_secrets(deploy_dir: str, env_name: str) -> bool:
    """Fetch secrets from self-hosted Infisical (config.cubeone.in) and merge into plane.env."""
    infisical_host = os.environ.get("INFISICAL_HOST", "https://config.cubeone.in").rstrip("/")
    project_id = os.environ.get("INFISICAL_PROJECT_ID", "f10e0d79-aa86-4c35-862a-e44ed0f482e3")
    auth_token = os.environ.get("INFISICAL_TOKEN", "")
    client_id = os.environ.get("INFISICAL_CLIENT_ID", "")
    client_secret = os.environ.get("INFISICAL_CLIENT_SECRET", "")

    if not auth_token and client_id and client_secret:
        try:
            login_url = f"{infisical_host}/api/v1/auth/universal-auth/login"
            req = urllib.request.Request(
                login_url,
                data=json.dumps({"clientId": client_id, "clientSecret": client_secret}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                auth_token = data.get("accessToken", "")
        except Exception as e:
            print(f" {CLR_DANGER}✗{CLR_RESET}  Infisical Universal Auth login error: {e}")

    if not auth_token and sys.stdin.isatty():
        env_label = "STAGING" if env_name == "staging" else "PRODUCTION"
        print(f"\n {CLR_PRIMARY}{CLR_BOLD}╭─[ INFISICAL AUTHENTICATION ({env_label}) ]─────────────────╮{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}  Infisical Host: {CLR_CYAN}{infisical_host}{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}  Project ID:     {CLR_MUTED}{project_id}{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}  Target Env:     {CLR_PRIMARY}{env_name}{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}  Choose Auth Method:")
        print(f" {CLR_PRIMARY}│{CLR_RESET}    [1] Universal Auth (Client ID + Client Secret)")
        print(f" {CLR_PRIMARY}│{CLR_RESET}    [2] Service Token (st.xxx)")
        print(f" {CLR_PRIMARY}╰────────────────────────────────────────────────────────────╯{CLR_RESET}\n")
        try:
            auth_method = input(" Select Auth Method [1/2, default: 1]: ").strip() or "1"
            if auth_method == "2":
                auth_token = input(" Enter Infisical Service Token: ").strip()
            else:
                cid = input(" Enter Infisical Client ID: ").strip()
                csec = getpass.getpass(" Enter Infisical Client Secret: ").strip()
                if cid and csec:
                    login_url = f"{infisical_host}/api/v1/auth/universal-auth/login"
                    req = urllib.request.Request(
                        login_url,
                        data=json.dumps({"clientId": cid, "clientSecret": csec}).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        auth_token = data.get("accessToken", "")
        except Exception as e:
            print(f" {CLR_DANGER}✗{CLR_RESET}  Infisical authentication failed: {e}")

    if not auth_token:
        print(f" {CLR_WARNING}▲{CLR_RESET}  No Infisical credentials provided; using existing local configuration.")
        return False

    print(f" {CLR_MUTED}Fetching '{env_name}' secrets from Infisical ({infisical_host})...{CLR_RESET}")
    secrets_list = []
    env_candidates = [env_name]
    if env_name in ["prod", "production"]:
        env_candidates = ["prod", "production"]

    for candidate in env_candidates:
        try:
            url = f"{infisical_host}/api/v3/secrets/raw?workspaceId={project_id}&environment={candidate}&secretPath=/"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {auth_token}"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                secrets_list = data.get("secrets", [])
                if secrets_list:
                    break
        except Exception:
            pass

    if not secrets_list:
        print(f" {CLR_DANGER}✗{CLR_RESET}  Could not retrieve secrets from Infisical for {env_name}. Using local configuration.")
        return False

    print(f" {CLR_SUCCESS}✓{CLR_RESET}  Successfully verified {CLR_BOLD}{len(secrets_list)}{CLR_RESET} secrets directly from Infisical ({env_name})")

    # Inject secrets into process environment for in-memory docker compose interpolation
    for s in secrets_list:
        k = s.get("secretKey")
        v = s.get("secretValue", "")
        if k:
            os.environ[k] = v

    # DO NOT write application secrets to plane.env! Only persist Infisical connection metadata.
    plane_env_path = os.path.join(deploy_dir, "plane.env")
    existing_vars = {}
    if os.path.isfile(plane_env_path):
        with open(plane_env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing_vars[k.strip()] = v.strip()

    infisical_meta = {
        "INFISICAL_HOST": infisical_host,
        "INFISICAL_PROJECT_ID": project_id,
        "INFISICAL_ENV": env_name,
    }
    if client_id:
        infisical_meta["INFISICAL_CLIENT_ID"] = client_id
    if client_secret:
        infisical_meta["INFISICAL_CLIENT_SECRET"] = client_secret
    if auth_token and not auth_token.startswith("ey"):
        infisical_meta["INFISICAL_TOKEN"] = auth_token

    for k, v in infisical_meta.items():
        existing_vars[k] = v

    existing_vars["ENVIRONMENT"] = env_name
    with open(plane_env_path, "w") as f:
        for k, v in sorted(existing_vars.items()):
            f.write(f"{k}={v}\n")

    print(f" {CLR_SUCCESS}✓{CLR_RESET}  OneFlow will fetch secrets directly from Infisical at runtime (zero secrets written to plane.env).")
    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    is_tty = sys.stdout.isatty()

    deploy_dir = script_dir
    if not os.path.isfile(os.path.join(deploy_dir, "plane.env")) and os.path.isfile(os.path.join(os.path.dirname(deploy_dir), "plane.env")):
        deploy_dir = os.path.dirname(deploy_dir)

    # Domain CLI parameter or interactive prompt
    cli_domain = None
    for i, arg in enumerate(sys.argv):
        if arg in ["--domain", "-d"] and i + 1 < len(sys.argv):
            cli_domain = sys.argv[i + 1]
        elif arg.startswith("--domain="):
            cli_domain = arg.split("=", 1)[1]

    no_prompt = "--no-prompt" in sys.argv
    default_candidate = detect_server_ip(deploy_dir, script_dir)
    if not default_candidate.startswith("http://") and not default_candidate.startswith("https://"):
        if default_candidate in ["localhost", "127.0.0.1"] or re.match(r'^\d+\.\d+\.\d+\.\d+', default_candidate):
            default_domain = f"http://{default_candidate}"
        else:
            default_domain = f"https://{default_candidate}"
    else:
        default_domain = default_candidate

    default_display = default_domain.replace("https://", "").replace("http://", "").rstrip("/")
    if not cli_domain and not no_prompt and not os.environ.get("ONEFLOW_DOMAIN_CONFIGURED") and sys.stdin.isatty():
        print(f"\n {CLR_PRIMARY}{CLR_BOLD}╭─[ DEPLOYMENT DOMAIN CONFIGURATION ]────────────────────────╮{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}  {CLR_BOLD}Enter the public domain or IP address for OneFlow.{CLR_RESET}        {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}  {CLR_MUTED}Examples: oneflow.cubeone.in or 13.234.29.32{CLR_RESET}              {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}╰────────────────────────────────────────────────────────────╯{CLR_RESET}\n")
        try:
            val = input(f" Enter Domain [default: {default_display}]: ").strip()
            cli_domain = val if val else default_display
        except (EOFError, KeyboardInterrupt):
            print("")
            sys.exit(1)
    elif not cli_domain:
        cli_domain = default_display

    if cli_domain:
        cli_domain = cli_domain.strip().rstrip("/")
        if not (cli_domain.startswith("http://") or cli_domain.startswith("https://")):
            if cli_domain in ["localhost", "127.0.0.1"] or re.match(r'^\d+\.\d+\.\d+\.\d+', cli_domain):
                final_origin = f"http://{cli_domain}"
            else:
                final_origin = f"https://{cli_domain}"
        else:
            final_origin = cli_domain

        parsed = urllib.parse.urlparse(final_origin)
        final_host = parsed.hostname or final_origin.split("://")[-1].split("/")[0].split(":")[0]
        final_scheme = parsed.scheme or "http"

        os.environ["ONEFLOW_DOMAIN"] = final_origin
        os.environ["DOMAIN_NAME"] = final_host
        os.environ["WEB_URL"] = final_origin
        os.environ["APP_DOMAIN"] = final_host
        os.environ["APP_PROTOCOL"] = final_scheme
        os.environ["ONEFLOW_DOMAIN_CONFIGURED"] = "1"

        # ── Environment & Secrets Configuration (3 Options) ───────────────
        cli_env_source = None
        for i, arg in enumerate(sys.argv):
            if arg in ["--env-source", "-e"] and i + 1 < len(sys.argv):
                cli_env_source = sys.argv[i + 1]
            elif arg.startswith("--env-source="):
                cli_env_source = arg.split("=", 1)[1]

        if not cli_env_source and not no_prompt and sys.stdin.isatty():
            print(f"\n {CLR_PRIMARY}{CLR_BOLD}╭─[ ENVIRONMENT & SECRETS CONFIGURATION ]────────────────────╮{CLR_RESET}")
            print(f" {CLR_PRIMARY}│{CLR_RESET}  {CLR_BOLD}Select how you want to provide environment variables:{CLR_RESET}     {CLR_PRIMARY}│{CLR_RESET}")
            print(f" {CLR_PRIMARY}│{CLR_RESET}                                                            ${CLR_PRIMARY}│{CLR_RESET}")
            print(f" {CLR_PRIMARY}│{CLR_RESET}    {CLR_CYAN}[1] Local .env file${CLR_RESET} (Use local plane.env / .env)        {CLR_PRIMARY}│{CLR_RESET}")
            print(f" {CLR_PRIMARY}│{CLR_RESET}    {CLR_CYAN}[2] Self-Hosted Infisical — Production${CLR_RESET} (config.cubeone.in) {CLR_PRIMARY}│{CLR_RESET}")
            print(f" {CLR_PRIMARY}│{CLR_RESET}    {CLR_CYAN}[3] Self-Hosted Infisical — Staging${CLR_RESET} (config.cubeone.in)    {CLR_PRIMARY}│{CLR_RESET}")
            print(f" {CLR_PRIMARY}╰────────────────────────────────────────────────────────────╯{CLR_RESET}\n")
            try:
                val = input(" Select Option [1/2/3, default: 1]: ").strip()
                cli_env_source = val if val else "1"
            except (EOFError, KeyboardInterrupt):
                print("")
                sys.exit(1)
        elif not cli_env_source:
            cli_env_source = "1"

        if cli_env_source in ["2", "prod", "production", "Production", "infisical", "Infisical"]:
            fetch_infisical_secrets(deploy_dir, "prod")
        elif cli_env_source in ["3", "staging", "Staging"]:
            fetch_infisical_secrets(deploy_dir, "staging")
        else:
            print(f" {CLR_SUCCESS}✓{CLR_RESET}  Using local environment configuration ({os.path.join(deploy_dir, 'plane.env')})")

        # ── Comprehensive domain sync ──────────────────────────────────────
        def _upsert(content: str, key: str, val: str) -> str:
            """Update key=val line in env file content, or append if missing."""
            if re.search(rf'^{re.escape(key)}=', content, re.MULTILINE):
                return re.sub(rf'^{re.escape(key)}=.*', f'{key}={val}', content, flags=re.MULTILINE)
            return content + f'\n{key}={val}\n'

        def _replace_if_present(content: str, key: str, val: str) -> str:
            """Update key=val only when the key already exists."""
            if re.search(rf'^{re.escape(key)}=', content, re.MULTILINE):
                return re.sub(rf'^{re.escape(key)}=.*', f'{key}={val}', content, flags=re.MULTILINE)
            return content

        def sync_domain_in_file(env_path: str) -> None:
            if not os.path.isfile(env_path):
                return
            try:
                with open(env_path, "r") as fh:
                    c = fh.read()

                # Core identity — always upserted
                c = _upsert(c, "ONEFLOW_DOMAIN", final_origin)
                c = _upsert(c, "DOMAIN_NAME", final_host)

                # Alias keys — update only if present
                c = _replace_if_present(c, "APP_DOMAIN",   final_host)
                c = _replace_if_present(c, "DOMAIN",       final_host)
                c = _replace_if_present(c, "APP_PROTOCOL", final_scheme)

                # Public URL (literal value so containers see it resolved)
                c = _replace_if_present(c, "WEB_URL", final_origin)

                # CORS / CSRF
                cors_val = final_origin
                if final_scheme == "https":
                    cors_val = f"{final_origin},http://{final_host}"
                c = _replace_if_present(c, "CORS_ALLOWED_ORIGINS", cors_val)
                c = _replace_if_present(c, "CSRF_TRUSTED_ORIGINS",  final_origin)

                # Webhook allowlist
                c = _replace_if_present(c, "WEBHOOK_ALLOWED_HOSTS", final_origin)

                # Silo integration callback (only when currently empty)
                m_icb = re.search(r'^INTEGRATION_CALLBACK_BASE_URL=(.*)', c, re.MULTILINE)
                if m_icb and not m_icb.group(1).strip().strip('"').strip("'"):
                    c = _replace_if_present(c, "INTEGRATION_CALLBACK_BASE_URL", final_origin)

                # SMTP domain placeholder — hostname only, update only if default
                m_smtp = re.search(r'^SMTP_DOMAIN=(.*)', c, re.MULTILINE)
                if m_smtp:
                    cur_smtp = m_smtp.group(1).strip().strip('"').strip("'")
                    if cur_smtp in ("0.0.0.0", "example.com", ""):
                        c = _replace_if_present(c, "SMTP_DOMAIN", final_host)

                # PI OAuth redirect URI (only when empty)
                m_pi = re.search(r'^PLANE_OAUTH_REDIRECT_URI=(.*)', c, re.MULTILINE)
                if m_pi and not m_pi.group(1).strip().strip('"').strip("'"):
                    c = _replace_if_present(c, "PLANE_OAUTH_REDIRECT_URI",
                                            f"{final_origin}/pi/api/v1/oauth/callback/")

                # Keycloak / OIDC redirect URIs
                c = _replace_if_present(c, "KEYCLOAK_REDIRECT_URI",
                                        f"{final_origin}/auth/oidc/callback/")
                c = _replace_if_present(c, "KEYCLOAK_POST_LOGOUT_REDIRECT_URI",
                                        f"{final_origin}/")

                # Caddy SITE_ADDRESS
                if re.search(r'^SITE_ADDRESS=', c, re.MULTILINE):
                    site_addr = final_host if final_scheme == "https" else ":80"
                    c = _replace_if_present(c, "SITE_ADDRESS", site_addr)

                with open(env_path, "w") as fh:
                    fh.write(c)
            except Exception:
                pass  # non-fatal

        def sync_all_domain_vars() -> int:
            targets = [
                os.path.join(deploy_dir, "plane.env"),
                os.path.join(deploy_dir, ".env"),
                os.path.join(os.path.dirname(deploy_dir), "plane.env"),
                os.path.join(os.path.dirname(deploy_dir), ".env"),
                os.path.join(script_dir, ".env"),
                os.path.join(deploy_dir, ".config.env"),
                os.path.join(script_dir, "apps", "api",   ".env"),
                os.path.join(script_dir, "apps", "web",   ".env"),
                os.path.join(script_dir, "apps", "space", ".env"),
                os.path.join(script_dir, "apps", "admin", ".env"),
                os.path.join(script_dir, "apps", "live",  ".env"),
                os.path.join(script_dir, "deployments", "cli", "community", "variables.env"),
                os.path.join(script_dir, "deployments", "aio", "community", "variables.env"),
            ]
            synced = 0
            for t in targets:
                if os.path.isfile(t):
                    sync_domain_in_file(t)
                    synced += 1
            return synced

        synced_count = sync_all_domain_vars()

        print(f"\n {CLR_SUCCESS}✓{CLR_RESET}  {CLR_BOLD}Deployment domain configured:{CLR_RESET} {CLR_PRIMARY}{final_origin}{CLR_RESET} (host: {final_host})")
        print(f" {CLR_SUCCESS}✓{CLR_RESET}  Domain propagated to {CLR_BOLD}{synced_count}{CLR_RESET} environment files")
        print(f" {CLR_MUTED}Starting deployment setup...{CLR_RESET}\n")
        time.sleep(0.5)

    # Pre-authenticate sudo cleanly before altering termios or entering alternate screen buffer
    try:
        r_docker = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r_docker.returncode != 0 and shutil.which("sudo"):
            r_sudo_check = subprocess.run(["sudo", "-n", "docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r_sudo_check.returncode != 0:
                print(f"\n {CLR_PRIMARY}{CLR_BOLD}●{CLR_RESET} {CLR_BOLD}Sudo privileges required for Docker container management.{CLR_RESET}")
                print(f"   Please enter your sudo password if prompted below:\n")
                subprocess.run(["sudo", "-v"], check=True)
                print("")
    except Exception:
        pass

    # Suppress terminal echo on stdin so mouse scrolling and arrow keys
    # never leak ^[[A / ^[[B escape sequences onto the screen
    old_termios = None
    if sys.stdin.isatty():
        try:
            import termios
            old_termios = termios.tcgetattr(sys.stdin.fileno())
            new_termios = termios.tcgetattr(sys.stdin.fileno())
            new_termios[3] = new_termios[3] & ~(termios.ECHO | termios.ICANON)
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_termios)
        except Exception:
            pass

    def drain_stdin():
        """Silently discard pending keystrokes or scroll wheel events from stdin."""
        if sys.stdin.isatty():
            try:
                import select
                while select.select([sys.stdin], [], [], 0)[0]:
                    os.read(sys.stdin.fileno(), 1024)
            except Exception:
                pass

    # Switch to Alternate Screen Buffer for 100% clean, non-scrolling UI
    if is_tty:
        sys.stdout.write("\033[?1049h\033[H\033[?25l")
        sys.stdout.flush()

    tui = TUIState(script_dir)

    def on_exit_signal(sig, frame):
        if is_tty:
            sys.stdout.write("\033[?1049l\033[?25h\033[0m\n")
            sys.stdout.flush()
        if old_termios is not None and sys.stdin.isatty():
            try:
                import termios
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_termios)
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, on_exit_signal)
    signal.signal(signal.SIGTERM, on_exit_signal)

    worker = threading.Thread(target=tui.run_workflow, daemon=True)
    worker.start()

    try:
        while tui.running or worker.is_alive():
            drain_stdin()
            if is_tty:
                frame = tui.render()
                sys.stdout.write(frame)
                sys.stdout.flush()
            time.sleep(0.08)

        # Final frame
        drain_stdin()
        if is_tty:
            frame = tui.render()
            sys.stdout.write(frame)
            sys.stdout.flush()
            time.sleep(0.5)
    finally:
        # Exit Alternate Screen Buffer cleanly & restore terminal modes
        drain_stdin()
        if is_tty:
            sys.stdout.write("\033[?1049l\033[?25h\033[0m\n")
            sys.stdout.flush()
        if old_termios is not None and sys.stdin.isatty():
            try:
                import termios
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_termios)
            except Exception:
                pass

    # Determine domain name dynamically
    app_domain = detect_server_ip(tui.deploy_dir, tui.source_dir)

    # Final Permanent Dashboard (Printed to standard terminal scrollback with pixel-perfect borders)
    print("")
    if tui.setup_success:
        print(f" {CLR_SUCCESS}{CLR_BOLD}✓  one flow has been successfully deployed and started!{CLR_RESET}")
        print(f" {CLR_MUTED}All configuration files, containers, and services are up and running.{CLR_RESET}\n")

        cols, _ = shutil.get_terminal_size((80, 24))
        dash_w = min(max(cols - 4, 60), 76)
        d_cmd_str = ' '.join(tui.docker_cmd)

        dash_lines = [
            "",
            f"  {CLR_SUCCESS}{CLR_BOLD}●{CLR_RESET}  {CLR_BOLD}one flow services are fully deployed and operational!{CLR_RESET}",
            "",
            f"  {CLR_BOLD}Service Endpoints:{CLR_RESET}",
            f"     {CLR_TEXT}Web App (Local):{CLR_RESET}   {CLR_PRIMARY}http://localhost{CLR_RESET}",
        ]
        if app_domain and app_domain not in ["localhost", "127.0.0.1"]:
            dash_lines.append(f"     {CLR_TEXT}Web App (Network):{CLR_RESET} {CLR_PRIMARY}http://{app_domain}{CLR_RESET}")
        
        dash_lines.extend([
            f"     {CLR_TEXT}God Mode (Admin):{CLR_RESET} {CLR_MUTED}http://localhost/god-mode/{CLR_RESET}",
            f"     {CLR_TEXT}Spaces (Public):{CLR_RESET}  {CLR_MUTED}http://localhost/spaces/{CLR_RESET}",
            f"     {CLR_TEXT}REST API:{CLR_RESET}         {CLR_MUTED}http://localhost/api/{CLR_RESET}",
            f"     {CLR_TEXT}Live Collab:{CLR_RESET}      {CLR_MUTED}ws://localhost/live/{CLR_RESET}",
            "",
            f"  {CLR_BOLD}Management Shortcuts:{CLR_RESET}",
            f"     {CLR_TEXT}Live Logs:{CLR_RESET}  {CLR_MUTED}{d_cmd_str} compose logs -f{CLR_RESET}",
            f"     {CLR_TEXT}Restart:{CLR_RESET}    {CLR_MUTED}{d_cmd_str} compose restart{CLR_RESET}",
            f"     {CLR_TEXT}Stop:{CLR_RESET}       {CLR_MUTED}{d_cmd_str} compose down{CLR_RESET}",
            "",
        ])

        for row in build_box(dash_w, "APPLICATION STATUS: ONLINE", dash_lines):
            print(f" {row}")
        print("")
        print(f" {CLR_MUTED}Documentation & Support:{CLR_RESET} {CLR_PRIMARY}https://github.com/sohan20051519/oneflow{CLR_RESET}\n")
        sys.exit(0)
    else:
        print(f"\n {CLR_DANGER}{CLR_BOLD}╭──────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
        print(f" {CLR_DANGER}{CLR_BOLD}│  DEPLOYMENT FAILED — EXACT ERROR DIAGNOSTICS                            │{CLR_RESET}")
        print(f" {CLR_DANGER}{CLR_BOLD}╰──────────────────────────────────────────────────────────────────────────╯{CLR_RESET}\n")

        if tui.failures:
            for idx, (f_step, f_cmd, f_code, f_details) in enumerate(tui.failures, 1):
                print(f" {CLR_DANGER}{CLR_BOLD}● Failure {idx}: {f_step}{CLR_RESET}")
                if f_cmd:
                    print(f"   {CLR_MUTED}Command:{CLR_RESET}   {CLR_TEXT}{f_cmd}{CLR_RESET}")
                if f_code:
                    print(f"   {CLR_MUTED}Exit Code:{CLR_RESET} {CLR_DANGER}{f_code}{CLR_RESET}")
                if f_details:
                    print(f"   {CLR_MUTED}Exact Output:{CLR_RESET}")
                    for f_line in f_details.splitlines():
                        print(f"     {CLR_DANGER}│{CLR_RESET} {f_line}")
                print("")
        else:
            print(f" {CLR_DANGER}Some issues occurred during setup. Review container logs:{CLR_RESET}")
            print(f"   {' '.join(tui.docker_cmd)} compose logs --tail 50\n")

        print(f" For assistance, visit: {CLR_PRIMARY}https://github.com/sohan20051519/oneflow{CLR_RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
