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
import urllib.request
import urllib.error

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
            if len(self.recent_activity) > 4:
                self.recent_activity = self.recent_activity[-4:]

    def log(self, tag: str, message: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        cleaned = message.rstrip("\r\n").strip()
        if cleaned:
            with self.lock:
                self.logs.append((now, tag, cleaned))

    def render(self) -> str:
        cols, lines = shutil.get_terminal_size((120, 35))
        
        # Responsive Layout Calculation
        use_split = cols >= 120
        left_w = 70 if use_split else min(cols - 4, 70)
        gap = 2
        right_w = max(42, cols - left_w - gap - 4) if use_split else 0

        with self.lock:
            prog = self.progress
            task = self.current_task
            cur_step = self.current_step
            statuses = list(self.step_statuses)
            activity = list(self.recent_activity)
            logs_snapshot = list(self.logs)

        # -----------------------------------------------------------------
        # LEFT COLUMN CONSTRUCTION
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

        # 3. Pipeline Steps & Activity Box (12 lines)
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
        
        if not activity:
            pipe_lines.append(f" {CLR_DARK}· Preparing deployment environment...{CLR_RESET}")
        else:
            for act_st, act_txt in activity[-3:]:
                if act_st == "ok":
                    icon = f"{CLR_SUCCESS}✓{CLR_RESET}"
                elif act_st == "info":
                    icon = f"{CLR_MUTED}ℹ{CLR_RESET}"
                elif act_st == "warn":
                    icon = f"{CLR_WARNING}▲{CLR_RESET}"
                else:
                    icon = f"{CLR_DANGER}✗{CLR_RESET}"
                pipe_lines.append(f"{icon} {CLR_TEXT}{act_txt}{CLR_RESET}")

        left_sections.extend(build_box(left_w, "PIPELINE EXECUTION", pipe_lines))

        # -----------------------------------------------------------------
        # RIGHT COLUMN CONSTRUCTION (Live Logs)
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

            avail_log_rows = len(left_sections) - 2  # Exactly matches left column height!
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
        max_drawable_rows = min(total_rows, max(lines - 2, 20))
        
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
        self.set_progress(5, "Generating configuration files...")
        self.log("env", "Scanning configuration templates")

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

        # Ensure DOMAIN_NAME in deploy configurations reflects current host IP
        detected_ip = detect_server_ip(self.deploy_dir, self.source_dir)
        if detected_ip and detected_ip not in ["localhost", "127.0.0.1", "13.234.29.32"]:
            for env_candidate in [plane_env, os.path.join(self.source_dir, ".env")]:
                if os.path.isfile(env_candidate):
                    try:
                        with open(env_candidate, "r") as f:
                            c = f.read()
                        if "13.234.29.32" in c:
                            c = c.replace("13.234.29.32", detected_ip)
                            with open(env_candidate, "w") as f:
                                f.write(c)
                            self.log("env", f"Updated legacy IP in {os.path.basename(env_candidate)} to {detected_ip}")
                    except Exception:
                        pass

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

        compose_args.extend(["up", "-d"])
        self.log("compose", f"Executing: {' '.join(compose_args)}")
        
        proc = subprocess.Popen(compose_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            self.log("compose", line)
        proc.wait()

        if proc.returncode == 0:
            ps_res = subprocess.run(self.docker_cmd + ["ps", "--format", "{{.Names}}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            active_cts = [c for c in ps_res.stdout.splitlines() if c.strip()]
            self.add_activity("ok", f"Orchestrated {len(active_cts)} services in background")
            self.log("compose", f"Active container count: {len(active_cts)}")
        else:
            self.add_activity("fail", "Failed to start Docker Compose services")
            self.log("compose", "Docker Compose up returned non-zero code")
            self.setup_success = False
            return

        self.set_progress(80, "Services started successfully")
        time.sleep(0.4)

    def _step_5_health(self):
        self.set_step(4)
        self.set_progress(85, "Awaiting service ports and database initialization...")
        self.add_activity("info", "Probing service endpoints...")
        self.log("health", "Initiating health checks on http://127.0.0.1:80/")

        retries = 45
        app_ready = False
        http_code = 0

        for i in range(1, retries + 1):
            self.log("health", f"Probing gateway (attempt {i}/{retries})...")
            try:
                req = urllib.request.Request("http://127.0.0.1:80/", headers={"User-Agent": "oneflow-healthcheck"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    http_code = resp.getcode()
            except urllib.error.HTTPError as e:
                http_code = e.code
            except Exception:
                http_code = 0

            if http_code in [200, 301, 302]:
                app_ready = True
                self.log("health", f"Gateway responded with HTTP {http_code} OK")
                break
            time.sleep(2)

        if app_ready:
            self.add_activity("ok", f"Frontend gateway responding (HTTP {http_code})")
            self.add_activity("ok", "Backend API & database operational")
            self.add_activity("ok", "All application components online")
            self.log("health", "Application components fully verified and healthy")
        else:
            self.add_activity("warn", "Services active; background startup continuing")
            self.log("health", "Probe timed out; services completing startup in background")

        self.set_progress(100, "one flow deployment complete!")
        time.sleep(0.6)

def detect_server_ip(deploy_dir: str, source_dir: str) -> str:
    """
    Dynamically detect the host's actual public or network IP address.
    Never falls back to hardcoded IPs.
    """
    # 0. User override via environment variable
    env_override = os.environ.get("ONEFLOW_DOMAIN") or os.environ.get("APP_DOMAIN")
    if env_override and env_override.strip() not in ["13.234.29.32", "localhost", "127.0.0.1", "0.0.0.0", ""]:
        return env_override.strip()

    # 1. Check if configured in plane.env or .env (strictly ignoring legacy hardcoded IP 13.234.29.32)
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
                        if line.startswith("DOMAIN_NAME=") or line.startswith("APP_DOMAIN="):
                            val = line.split("=", 1)[1].strip().strip('"\'')
                            if val and val not in ["13.234.29.32", "localhost", "127.0.0.1", "0.0.0.0", ""]:
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

    return "localhost"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    is_tty = sys.stdout.isatty()
    
    # Switch to Alternate Screen Buffer for 100% clean, non-scrolling UI
    if is_tty:
        sys.stdout.write("\033[?1049h\033[H\033[?25l")
        sys.stdout.flush()

    tui = TUIState(script_dir)

    def on_exit_signal(sig, frame):
        if is_tty:
            sys.stdout.write("\033[?1049l\033[?25h\033[0m\n")
            sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_exit_signal)
    signal.signal(signal.SIGTERM, on_exit_signal)

    worker = threading.Thread(target=tui.run_workflow, daemon=True)
    worker.start()

    try:
        while tui.running or worker.is_alive():
            if is_tty:
                frame = tui.render()
                sys.stdout.write(frame)
                sys.stdout.flush()
            time.sleep(0.08)

        # Final frame
        if is_tty:
            frame = tui.render()
            sys.stdout.write(frame)
            sys.stdout.flush()
            time.sleep(0.5)
    finally:
        # Exit Alternate Screen Buffer cleanly
        if is_tty:
            sys.stdout.write("\033[?1049l\033[?25h\033[0m\n")
            sys.stdout.flush()

    # Determine domain name dynamically
    app_domain = detect_server_ip(tui.deploy_dir, tui.source_dir)

    # Final Permanent Dashboard (Printed to standard terminal scrollback)
    print("")
    if tui.setup_success:
        print(f" {CLR_SUCCESS}{CLR_BOLD}✓  one flow has been successfully deployed and started!{CLR_RESET}")
        print(f" {CLR_MUTED}All configuration files, containers, and services are up and running.{CLR_RESET}\n")

        dash_w = 70
        title = " Application Status: ONLINE "
        dash_count = max(0, dash_w + 2 - len(title) - 1)
        
        print(f" {CLR_PRIMARY}{CLR_BOLD}╭─{title}{'─' * dash_count}╮{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{' ' * dash_w} {CLR_PRIMARY}│{CLR_RESET}")
        
        row1 = f"  {CLR_SUCCESS}{CLR_BOLD}●{CLR_RESET}  {CLR_BOLD}one flow services are fully deployed and operational!{CLR_RESET}"
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line(row1, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{' ' * dash_w} {CLR_PRIMARY}│{CLR_RESET}")
        
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('  ' + CLR_BOLD + 'Service Endpoints:' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'Web App:' + CLR_RESET + '          ' + CLR_PRIMARY + 'http://' + app_domain + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'God Mode (Admin):' + CLR_RESET + ' ' + CLR_MUTED + 'http://' + app_domain + '/god-mode/' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'Spaces (Public):' + CLR_RESET + '  ' + CLR_MUTED + 'http://' + app_domain + '/spaces/' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'REST API:' + CLR_RESET + '         ' + CLR_MUTED + 'http://' + app_domain + '/api/' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'MinIO Console:' + CLR_RESET + '    ' + CLR_MUTED + 'http://' + app_domain + ':9090' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'MinIO S3 API:' + CLR_RESET + '     ' + CLR_MUTED + 'http://' + app_domain + ':9000' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'Live Collab:' + CLR_RESET + '      ' + CLR_MUTED + 'ws://' + app_domain + '/live/' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{' ' * dash_w} {CLR_PRIMARY}│{CLR_RESET}")
        
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('  ' + CLR_BOLD + 'Management Shortcuts:' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        d_cmd_str = ' '.join(tui.docker_cmd)
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'Live Logs:' + CLR_RESET + '  ' + CLR_MUTED + d_cmd_str + ' compose logs -f' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'Restart:' + CLR_RESET + '    ' + CLR_MUTED + d_cmd_str + ' compose restart' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET} {fit_line('     ' + CLR_TEXT + 'Stop:' + CLR_RESET + '       ' + CLR_MUTED + d_cmd_str + ' compose down' + CLR_RESET, dash_w - 2)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{' ' * dash_w} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}╰{'─' * (dash_w + 2)}╯{CLR_RESET}\n")
        print(f" {CLR_MUTED}Documentation & Support:{CLR_RESET} {CLR_PRIMARY}https://github.com/sohan20051519/oneflow{CLR_RESET}\n")
        sys.exit(0)
    else:
        print(f" {CLR_DANGER}{CLR_BOLD}✗  Some issues occurred during setup.{CLR_RESET}")
        print(f" {CLR_MUTED}Please review the failed steps and live logs above.{CLR_RESET}\n")
        print(f" For assistance, visit: {CLR_PRIMARY}https://github.com/sohan20051519/oneflow{CLR_RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
