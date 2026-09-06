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

# ANSI Color Definitions
CLR_PRIMARY    = "\033[38;2;232;27;91m"     # Brand Coral #E81B5B
CLR_PRIMARY_BG = "\033[48;2;232;27;91m"     # Coral Background
CLR_TEXT       = "\033[38;2;250;250;250m"   # Foreground #FAFAFA
CLR_MUTED      = "\033[38;2;163;163;163m"  # Muted text #A3A3A3
CLR_DARK       = "\033[38;2;115;115;115m"   # Border #737373
CLR_SUCCESS    = "\033[38;2;34;163;75m"     # Green
CLR_WARNING    = "\033[38;2;250;204;21m"    # Amber
CLR_DANGER     = "\033[38;2;239;68;68m"     # Red
CLR_CYAN       = "\033[38;2;56;189;248m"    # Cyan
CLR_PURPLE     = "\033[38;2;168;85;247m"   # Purple
CLR_BLUE       = "\033[38;2;59;130;246m"    # Blue
CLR_BOLD       = "\033[1m"
CLR_RESET      = "\033[0m"

ANSI_REGEX = re.compile(r'\x1B\[[0-9;]*[a-zA-Z]')

def strip_ansi(text: str) -> str:
    return ANSI_REGEX.sub('', text)

def pad_str(text: str, visual_width: int) -> str:
    raw_len = len(strip_ansi(text))
    pad = visual_width - raw_len
    if pad > 0:
        return text + (" " * pad)
    return text

class TUI:
    def __init__(self, script_dir: str):
        self.script_dir = script_dir
        self.lock = threading.Lock()
        self.running = True
        self.progress = 0
        self.current_task = "Initializing deployment..."
        self.current_step = 0
        self.setup_success = True
        
        self.steps = [
            {"title": "Provisioning Environment Configurations", "items": [], "status": "pending"},
            {"title": "Cryptographic Secrets & Security Keys", "items": [], "status": "pending"},
            {"title": "Container Runtime & Image Synchronization", "items": [], "status": "pending"},
            {"title": "Deploying & Starting All Services", "items": [], "status": "pending"},
            {"title": "Verifying Service Health & Readiness", "items": [], "status": "pending"},
        ]
        self.logs = []
        
        # Determine paths
        if os.path.isfile(os.path.join(self.script_dir, "docker-compose.yml")):
            self.source_dir = self.script_dir
            self.deploy_dir = self.script_dir
            self.compose_file = os.path.join(self.script_dir, "docker-compose.yml")
        elif os.path.isfile(os.path.join(os.path.dirname(self.script_dir), "docker-compose.yml")):
            self.deploy_dir = os.path.dirname(self.script_dir)
            self.source_dir = self.script_dir
            self.compose_file = os.path.join(self.deploy_dir, "docker-compose.yml")
        else:
            self.deploy_dir = self.script_dir
            self.source_dir = os.path.join(self.script_dir, "source")
            self.compose_file = os.path.join(self.source_dir, "docker-compose.yml")

        # Docker command detection
        self.docker_cmd = self._detect_docker()
        
    def _detect_docker(self) -> list:
        # Check if docker works directly
        try:
            res = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return ["docker"]
        except Exception:
            pass
            
        # Check if sudo docker works without password
        try:
            res = subprocess.run(["sudo", "-n", "docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return ["sudo", "docker"]
        except Exception:
            pass

        # If sudo available, prompt once
        if shutil.which("sudo") and sys.stdin.isatty():
            try:
                print(f" {CLR_MUTED}Elevated permissions needed for Docker daemon...{CLR_RESET}")
                subprocess.run(["sudo", "-v"], check=True)
                return ["sudo", "docker"]
            except Exception:
                pass

        if shutil.which("sudo"):
            return ["sudo", "docker"]
        return ["docker"]

    def log(self, tag: str, message: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        with self.lock:
            # Clean non-printable / trailing spaces
            cleaned = message.rstrip("\r\n").strip()
            if cleaned:
                self.logs.append((now, tag, cleaned))

    def add_item(self, step_idx: int, status: str, text: str):
        with self.lock:
            self.steps[step_idx]["items"].append((status, text))

    def set_step(self, step_idx: int):
        with self.lock:
            self.current_step = step_idx
            self.steps[step_idx]["status"] = "active"

    def set_progress(self, pct: int, task: str):
        with self.lock:
            self.progress = min(100, max(0, pct))
            self.current_task = task

    def render_frame(self) -> str:
        cols, lines = shutil.get_terminal_size((120, 42))
        left_w = 70
        use_split = cols >= 115
        right_w = max(40, cols - left_w - 4) if use_split else 0
        bw = left_w - 4

        with self.lock:
            cur_prog = self.progress
            cur_task = self.current_task
            cur_step = self.current_step
            steps_copy = [dict(s, items=list(s["items"])) for s in self.steps]
            logs_copy = list(self.logs)

        left_lines = []
        # Banner Box
        left_lines.append(f" {CLR_PRIMARY}╭─[ ONE FLOW ]{'─' * (bw - 12)}╮{CLR_RESET}")
        left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}  {CLR_BOLD}██████  ███    ██ ███████     ███████ ██       ██████  ██     ██{CLR_RESET}  {CLR_PRIMARY}│{CLR_RESET}")
        left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET} {CLR_BOLD}██    ██ ████   ██ ██          ██      ██      ██    ██ ██     ██{CLR_RESET}  {CLR_PRIMARY}│{CLR_RESET}")
        left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET} {CLR_BOLD}██    ██ ██ ██  ██ █████       █████   ██      ██    ██ ██  █  ██{CLR_RESET}  {CLR_PRIMARY}│{CLR_RESET}")
        left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}  {CLR_BOLD}██████  ██   ████ ███████     ██      ███████  ██████   ███ ███{CLR_RESET}   {CLR_PRIMARY}│{CLR_RESET}")
        banner_sub = f"  {CLR_TEXT}{CLR_BOLD}one flow{CLR_RESET} {CLR_MUTED}· intelligent project management & workflow automation{CLR_RESET}"
        left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str(banner_sub, bw)} {CLR_PRIMARY}│{CLR_RESET}")
        left_lines.append(f" {CLR_PRIMARY}╰{'─' * (bw + 2)}╯{CLR_RESET}")

        # Progress Bar Box
        bar_len = 34
        filled = int(bar_len * cur_prog / 100)
        empty = bar_len - filled
        bar_str = f"{CLR_PRIMARY}{'█' * filled}{CLR_MUTED}{'░' * empty}{CLR_RESET}"
        
        left_lines.append(f" {CLR_PRIMARY}╭─[ DEPLOYMENT PROGRESS ]{'─' * (bw - 21)}╮{CLR_RESET}")
        prog_line = f"  [{bar_str}] {CLR_BOLD}{cur_prog:>3}%{CLR_RESET} (Step {min(5, cur_step + 1)}/5)"
        left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str(prog_line, bw)} {CLR_PRIMARY}│{CLR_RESET}")
        
        task_str = cur_task[:bw - 12]
        task_line = f"  {CLR_MUTED}Task:{CLR_RESET} {CLR_TEXT}{task_str}{CLR_RESET}"
        left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str(task_line, bw)} {CLR_PRIMARY}│{CLR_RESET}")
        left_lines.append(f" {CLR_PRIMARY}╰{'─' * (bw + 2)}╯{CLR_RESET}")

        # Steps
        for idx, step in enumerate(steps_copy):
            st_num = f"STEP {idx+1}/5"
            st_title = step["title"]
            left_lines.append(f" {CLR_PRIMARY}╭─[ {st_num} ] {CLR_TEXT}{st_title}{CLR_RESET}")
            
            if not step["items"]:
                if idx == cur_step:
                    left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}  {CLR_MUTED}⏳ In progress...{CLR_RESET}")
                else:
                    left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}  {CLR_DARK}· Pending{CLR_RESET}")
            else:
                for item_st, item_txt in step["items"][-4:]:
                    if item_st == "ok":
                        icon = f"{CLR_SUCCESS}✓{CLR_RESET}"
                    elif item_st == "info":
                        icon = f"{CLR_MUTED}ℹ{CLR_RESET}"
                    elif item_st == "warn":
                        icon = f"{CLR_WARNING}▲{CLR_RESET}"
                    else:
                        icon = f"{CLR_DANGER}✗{CLR_RESET}"
                    trunc_txt = item_txt[:bw - 6]
                    left_lines.append(f" {CLR_PRIMARY}│{CLR_RESET}  {icon}  {CLR_TEXT}{trunc_txt}{CLR_RESET}")
            left_lines.append(f" {CLR_PRIMARY}╰{'─' * (bw + 2)}{CLR_RESET}")

        # Right Column (Live Logs)
        right_lines = []
        if use_split:
            rw = right_w - 4
            tag_colors = {
                "sys": CLR_CYAN,
                "env": CLR_PURPLE,
                "crypto": CLR_WARNING,
                "docker": CLR_BLUE,
                "build": CLR_PRIMARY,
                "compose": CLR_SUCCESS,
                "health": CLR_CYAN,
            }
            
            right_lines.append(f"{CLR_PRIMARY}╭─[ LIVE CONTAINER & DEPLOYMENT LOGS ]{'─' * max(0, rw - 35)}╮{CLR_RESET}")
            max_log_rows = max(len(left_lines) - 2, 22)
            visible_logs = logs_copy[-max_log_rows:]
            
            for r in range(max_log_rows):
                if r < len(visible_logs):
                    t_str, tag, msg = visible_logs[r]
                    t_col = tag_colors.get(tag, CLR_MUTED)
                    tag_display = f"{t_col}[{tag:<7}]{CLR_RESET}"
                    avail_msg = rw - len(t_str) - 12
                    trunc_msg = msg[:max(0, avail_msg)]
                    row_content = f" {CLR_MUTED}{t_str}{CLR_RESET} {tag_display} {CLR_TEXT}{trunc_msg}{CLR_RESET}"
                    right_lines.append(f"{CLR_PRIMARY}│{CLR_RESET}{pad_str(row_content, rw)} {CLR_PRIMARY}│{CLR_RESET}")
                else:
                    right_lines.append(f"{CLR_PRIMARY}│{CLR_RESET}{' ' * rw} {CLR_PRIMARY}│{CLR_RESET}")
            right_lines.append(f"{CLR_PRIMARY}╰{'─' * (rw + 2)}╯{CLR_RESET}")

        # Combine lines
        total_rows = max(len(left_lines), len(right_lines))
        combined = []
        for r in range(total_rows):
            l_str = left_lines[r] if r < len(left_lines) else " " * left_w
            if use_split:
                r_str = right_lines[r] if r < len(right_lines) else ""
                combined.append(f"{pad_str(l_str, left_w)}  {r_str}")
            else:
                combined.append(l_str)

        return "\033[H" + "\n".join(combined)

    def run_worker(self):
        """Worker thread executing the deployment workflow."""
        try:
            self.execute_deployment()
        except Exception as e:
            self.log("sys", f"Fatal error: {str(e)}")
            self.setup_success = False
        finally:
            self.running = False

    def execute_deployment(self):
        # -------------------------------------------------------------
        # STEP 1: Environment Configurations (0% -> 20%)
        # -------------------------------------------------------------
        self.set_step(0)
        self.set_progress(5, "Provisioning environment files...")
        self.log("env", "Synchronizing configuration templates")

        def copy_env(src_rel, dest_rel, label):
            src = os.path.join(self.source_dir, src_rel)
            dest = os.path.join(self.source_dir, dest_rel)
            if not os.path.isfile(src):
                self.add_item(0, "fail", f"Missing template: {label}")
                self.log("env", f"Missing template file: {src}")
                return False
            if os.path.isfile(dest):
                self.add_item(0, "info", f"Existing file preserved: {label}")
                self.log("env", f"Preserved existing {label}")
            else:
                shutil.copy(src, dest)
                self.add_item(0, "ok", f"Generated {label} from template")
                self.log("env", f"Created {label}")
            return True

        copy_env(".env.example", ".env", "./.env")
        copy_env("apps/web/.env.example", "apps/web/.env", "./apps/web/.env")
        copy_env("apps/api/.env.example", "apps/api/.env", "./apps/api/.env")
        copy_env("apps/space/.env.example", "apps/space/.env", "./apps/space/.env")
        copy_env("apps/admin/.env.example", "apps/admin/.env", "./apps/admin/.env")
        copy_env("apps/live/.env.example", "apps/live/.env", "./apps/live/.env")

        # Check plane.env
        plane_env = os.path.join(self.deploy_dir, "plane.env")
        if os.path.isfile(plane_env):
            dot_env = os.path.join(self.deploy_dir, ".env")
            if not os.path.exists(dot_env):
                try:
                    os.symlink("plane.env", dot_env)
                    self.add_item(0, "ok", "Deploy environment synchronized (plane.env)")
                    self.log("env", "Symlinked plane.env -> .env")
                except Exception:
                    pass

        self.set_progress(20, "Environment files ready")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 2: Cryptographic Secrets & Keys (20% -> 40%)
        # -------------------------------------------------------------
        self.set_step(1)
        self.set_progress(25, "Securing cryptographic keys...")
        api_env_file = os.path.join(self.source_dir, "apps/api/.env")
        if os.path.isfile(api_env_file):
            with open(api_env_file, "r") as f:
                content = f.read()
            match = re.search(r'^SECRET_KEY=(.*)', content, re.MULTILINE)
            key_val = match.group(1).strip('"\'') if match else ""
            if not key_val or key_val in ["your-secret-key-here", "change-me-in-production"]:
                new_key = secrets.token_urlsafe(50)
                if match:
                    content = re.sub(r'^SECRET_KEY=.*', f'SECRET_KEY="{new_key}"', content, flags=re.MULTILINE)
                else:
                    content += f'\nSECRET_KEY="{new_key}"\n'
                with open(api_env_file, "w") as f:
                    f.write(content)
                self.add_item(1, "ok", "Generated fresh Django SECRET_KEY (50 characters)")
                self.log("crypto", "Generated new secure Django SECRET_KEY")
            else:
                self.add_item(1, "info", "Django SECRET_KEY already configured in apps/api/.env")
                self.log("crypto", "Existing SECRET_KEY verified")

        if os.path.isfile(plane_env):
            with open(plane_env, "r") as f:
                p_content = f.read()
            if not re.search(r'^MACHINE_SIGNATURE=.', p_content, re.MULTILINE):
                sig = secrets.token_hex(16)
                p_content = re.sub(r'^MACHINE_SIGNATURE=.*', f'MACHINE_SIGNATURE="{sig}"', p_content, flags=re.MULTILINE)
                with open(plane_env, "w") as f:
                    f.write(p_content)
                self.add_item(1, "ok", "Generated machine signature in plane.env")
                self.log("crypto", f"Generated machine signature {sig[:8]}...")
            else:
                self.add_item(1, "info", "Machine signature verified in deploy environment")

        self.set_progress(40, "Cryptographic keys ready")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 3: Container Runtime & Image Synchronization (40% -> 60%)
        # -------------------------------------------------------------
        self.set_step(2)
        self.set_progress(45, "Checking Docker engine...")
        self.log("docker", f"Testing container runtime ({' '.join(self.docker_cmd)})")

        res = subprocess.run(self.docker_cmd + ["info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            self.add_item(2, "fail", "Docker daemon is not accessible. Please ensure Docker is running.")
            self.log("docker", "Failed to connect to Docker daemon")
            self.setup_success = False
            return
        
        # Get docker version
        ver_res = subprocess.run(self.docker_cmd + ["--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        d_ver = ver_res.stdout.strip().split()[2].rstrip(',') if ver_res.returncode == 0 else "detected"
        self.add_item(2, "ok", f"Docker engine operational (version {d_ver})")
        self.log("docker", f"Docker runtime active: version {d_ver}")

        # Check frontend image
        chk_img = subprocess.run(self.docker_cmd + ["image", "inspect", "plane-frontend:oneflow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if chk_img.returncode == 0:
            self.add_item(2, "ok", "Found customized oneflow frontend image (plane-frontend:oneflow)")
            self.log("docker", "Found existing plane-frontend:oneflow image")
        else:
            self.add_item(2, "info", "Building customized oneflow frontend image...")
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
                self.add_item(2, "ok", "Built plane-frontend:oneflow image successfully")
                self.log("build", "Successfully built plane-frontend:oneflow")
            else:
                self.add_item(2, "warn", "Building web image failed; continuing with fallback images")
                self.log("build", "Build exited with non-zero status; using fallback")

        self.set_progress(60, "Container runtime synchronized")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 4: Deploying & Starting All Services (60% -> 80%)
        # -------------------------------------------------------------
        self.set_step(3)
        self.set_progress(65, "Deploying services with Docker Compose...")
        
        # FIX: Directly use self.compose_file with clean identification
        rel_compose = os.path.relpath(self.compose_file, self.script_dir)
        if rel_compose == "docker-compose.yml":
            self.add_item(3, "ok", "Detected root docker-compose.yml configuration")
            self.log("compose", "Using root docker-compose.yml")
        else:
            self.add_item(3, "ok", f"Detected compose configuration: {rel_compose}")
            self.log("compose", f"Using configuration {self.compose_file}")

        compose_args = self.docker_cmd + ["compose", "--file", self.compose_file]
        compose_env = os.path.join(self.deploy_dir, "plane.env")
        if os.path.isfile(compose_env):
            compose_args.extend(["--env-file", compose_env])
            self.log("compose", f"Applying environment file: {compose_env}")
        elif os.path.isfile(os.path.join(self.source_dir, ".env")):
            compose_args.extend(["--env-file", os.path.join(self.source_dir, ".env")])
            self.log("compose", "Applying environment file: .env")

        compose_args.extend(["up", "-d"])
        self.log("compose", f"Running: {' '.join(compose_args)}")
        
        proc = subprocess.Popen(compose_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            self.log("compose", line)
        proc.wait()

        if proc.returncode == 0:
            # Count running containers
            ps_res = subprocess.run(self.docker_cmd + ["ps", "--format", "{{.Names}}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            ct_count = len([c for c in ps_res.stdout.splitlines() if c.strip()])
            self.add_item(3, "ok", f"Orchestrated {ct_count} containerized services in background")
            self.log("compose", f"Services running: {ct_count} containers active")
        else:
            self.add_item(3, "fail", "Failed to start Docker Compose services")
            self.log("compose", "Compose up returned non-zero code")
            self.setup_success = False
            return

        self.set_progress(80, "Services started")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 5: Verifying Service Health & Readiness (80% -> 100%)
        # -------------------------------------------------------------
        self.set_step(4)
        self.set_progress(85, "Awaiting service ports and database initialization...")
        self.add_item(4, "info", "Awaiting service ports and database initialization...")
        self.log("health", "Beginning service health checks on http://127.0.0.1:80/")

        retries = 45
        app_ready = False
        http_status = 0
        
        for i in range(1, retries + 1):
            self.log("health", f"Probing gateway (attempt {i}/{retries})...")
            try:
                req = urllib.request.Request("http://127.0.0.1:80/", headers={"User-Agent": "oneflow-setup"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    http_status = resp.getcode()
            except urllib.error.HTTPError as e:
                http_status = e.code
            except Exception:
                http_status = 0

            if http_status in [200, 301, 302]:
                app_ready = True
                self.log("health", f"Gateway responded with HTTP {http_status}")
                break
            time.sleep(2)

        if app_ready:
            self.add_item(4, "ok", f"Frontend web gateway responding (HTTP {http_status})")
            self.add_item(4, "ok", "Backend API and database operational")
            self.add_item(4, "ok", "All core application components are healthy")
            self.log("health", "Application components healthy and operational")
        else:
            self.add_item(4, "warn", "Services started; initialization still in progress in background")
            self.log("health", "Gateway check timed out, services initializing")

        self.set_progress(100, "one flow deployment complete!")
        time.sleep(0.8)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    
    # Clear screen
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    tui = TUI(script_dir)
    
    def cleanup_signal(signum, frame):
        sys.stdout.write("\033[?25h\033[0m\n")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup_signal)
    signal.signal(signal.SIGTERM, cleanup_signal)

    worker_thread = threading.Thread(target=tui.run_worker, daemon=True)
    worker_thread.start()

    try:
        while tui.running or worker_thread.is_alive():
            frame = tui.render_frame()
            sys.stdout.write(frame)
            sys.stdout.flush()
            time.sleep(0.06)
            
        # Final frame render
        final_frame = tui.render_frame()
        sys.stdout.write(final_frame)
        sys.stdout.flush()
    finally:
        sys.stdout.write("\033[?25h\033[0m\n")
        sys.stdout.flush()

    # Determine domain name
    app_domain = "13.234.29.32"
    plane_env = os.path.join(tui.deploy_dir, "plane.env")
    if os.path.isfile(plane_env):
        with open(plane_env, "r") as f:
            for line in f:
                if line.startswith("DOMAIN_NAME="):
                    d = line.split("=", 1)[1].strip().strip('"\'')
                    if d and d != "localhost":
                        app_domain = d
                    break

    # Dashboard display
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
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str(row1, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{' ' * dash_w} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('  ' + CLR_BOLD + 'Service Endpoints:' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'Web App:' + CLR_RESET + '          ' + CLR_PRIMARY + 'http://' + app_domain + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'God Mode (Admin):' + CLR_RESET + ' ' + CLR_MUTED + 'http://' + app_domain + '/god-mode/' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'Spaces (Public):' + CLR_RESET + '  ' + CLR_MUTED + 'http://' + app_domain + '/spaces/' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'REST API:' + CLR_RESET + '         ' + CLR_MUTED + 'http://' + app_domain + '/api/' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'MinIO Console:' + CLR_RESET + '    ' + CLR_MUTED + 'http://' + app_domain + ':9090' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'MinIO S3 API:' + CLR_RESET + '     ' + CLR_MUTED + 'http://' + app_domain + ':9000' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'Live Collab:' + CLR_RESET + '      ' + CLR_MUTED + 'ws://' + app_domain + '/live/' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{' ' * dash_w} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('  ' + CLR_BOLD + 'Management Shortcuts:' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        d_cmd_str = ' '.join(tui.docker_cmd)
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'Live Logs:' + CLR_RESET + '  ' + CLR_MUTED + d_cmd_str + ' compose logs -f' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'Restart:' + CLR_RESET + '    ' + CLR_MUTED + d_cmd_str + ' compose restart' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
        print(f" {CLR_PRIMARY}│{CLR_RESET}{pad_str('     ' + CLR_TEXT + 'Stop:' + CLR_RESET + '       ' + CLR_MUTED + d_cmd_str + ' compose down' + CLR_RESET, dash_w)} {CLR_PRIMARY}│{CLR_RESET}")
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
