#!/usr/bin/env python3
"""
███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗  ██╗
██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝╚██╗██╔╝
█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗   ╚███╔╝
██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝   ██╔██╗
███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗██╔╝ ██╗
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

        ⚡ EngineX v2.0 — Recon & Bug Bounty Framework ⚡
                     Developed by RAVX
"""

import os
import sys
import time
import json
import shutil
import signal
import platform
import argparse
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
#  DEPENDENCY BOOTSTRAP — runs before everything
# ─────────────────────────────────────────────
def _bootstrap_pip_packages():
    """
    Ensure third-party pip packages are available.
    Installs into user site-packages so no sudo is needed.
    Works inside virtual-envs, system Python, and externally-managed
    Debian/Ubuntu environments (PEP 668 'externally-managed').
    """
    required = {
        "requests": "requests",
        "colorama": "colorama",
        "tqdm":     "tqdm",
    }

    # Try importing; collect what's missing
    missing = []
    for import_name, pkg_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg_name)

    if not missing:
        return  # all good

    print(f"[*] Auto-installing missing Python packages: {', '.join(missing)}")

    # Base install command — always use --user so no sudo needed
    base_cmd = [sys.executable, "-m", "pip", "install", "--user", "--quiet"]

    for pkg in missing:
        cmd = base_cmd + [pkg]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # PEP 668: externally managed env (Debian/Ubuntu 23+)
            if "externally-managed" in result.stderr:
                print(f"    [!] Externally-managed env detected. Retrying with --break-system-packages …")
                cmd_ext = base_cmd + ["--break-system-packages", pkg]
                result2 = subprocess.run(cmd_ext, capture_output=True, text=True)
                if result2.returncode != 0:
                    print(f"    [ERROR] Could not install {pkg}:\n{result2.stderr.strip()}")
                    sys.exit(1)
            else:
                print(f"    [ERROR] Could not install {pkg}:\n{result.stderr.strip()}")
                sys.exit(1)

    # Reload site-packages so the freshly installed modules are importable
    import importlib
    import site
    importlib.invalidate_caches()
    # Ensure --user site is on the path (needed when not in a venv)
    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.insert(0, user_site)

    print("[✓] Packages ready.\n")

_bootstrap_pip_packages()

# ─────────────────────────────────────────────
#  NOW safe to import third-party libraries
# ─────────────────────────────────────────────
import requests                          # noqa: E402
from colorama import Fore, Style, init   # noqa: E402
from tqdm import tqdm                    # noqa: E402

init(autoreset=True)  # colorama auto-reset after each print

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
OUTPUT_DIR   = "output"
WORDLIST_DIR = "wordlists"
LOG_FILE     = "enginex.log"
STATUS_FILE  = "status.txt"
PAUSE_FILE   = "pause.flag"
DEFAULT_RATE = 50
TIMEOUT      = 8   # seconds for HTTP requests

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("enginex")


# ─────────────────────────────────────────────
#  SIGNAL HANDLER (Ctrl+C graceful exit)
# ─────────────────────────────────────────────
def _sig_handler(sig, frame):
    print(f"\n{Fore.YELLOW}[!] Interrupted. Partial results saved in {OUTPUT_DIR}/")
    sys.exit(0)

signal.signal(signal.SIGINT, _sig_handler)


# ─────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────
def banner():
    print(Fore.CYAN + Style.BRIGHT + r"""
███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗  ██╗
██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝╚██╗██╔╝
█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗   ╚███╔╝
██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝   ██╔██╗
███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗██╔╝ ██╗
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
""")
    print(Fore.GREEN + "        ⚡ EngineX v2.0 — Recon & Bug Bounty Framework ⚡")
    print(Fore.WHITE + "                     Developed by RAVX\n")
    print(Fore.YELLOW + f"[System] {platform.system()} {platform.release()} | {platform.machine()}")
    print(Fore.YELLOW + f"[Python] {platform.python_version()}")
    print(Fore.YELLOW + f"[Time]   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


# ─────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────
def log_info(msg: str):
    logger.info(Fore.CYAN + msg)

def log_ok(msg: str):
    logger.info(Fore.GREEN + "[✓] " + msg)

def log_warn(msg: str):
    logger.warning(Fore.YELLOW + "[!] " + msg)

def log_err(msg: str):
    logger.error(Fore.RED + "[✗] " + msg)

def update_status(s: str):
    Path(STATUS_FILE).write_text(s)

def check_pause():
    while Path(PAUSE_FILE).exists():
        log_warn("PAUSED — remove pause.flag to continue")
        time.sleep(5)

def safe_read_lines(filepath: str) -> list:
    """Return stripped non-empty lines, empty list if file missing."""
    p = Path(filepath)
    if not p.exists():
        log_warn(f"File not found: {filepath}")
        return []
    return [l.strip() for l in p.read_text(errors="ignore").splitlines() if l.strip()]

def run_cmd(cmd: str, rate: int = DEFAULT_RATE):
    """Run a shell command with rate-limit sleep, log it."""
    log_info(f"CMD → {cmd}")
    ret = os.system(cmd)
    if ret != 0:
        log_warn(f"Command exited with code {ret}: {cmd[:80]}")
    time.sleep(1 / max(rate, 1))
    return ret

def ensure_dirs(*dirs):
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
#  GO TOOL INSTALLER
# ─────────────────────────────────────────────
def _go_available() -> bool:
    return shutil.which("go") is not None

def _install_go_tool(name: str, repo: str):
    if shutil.which(name):
        log_ok(f"{name} already installed")
        return
    if not _go_available():
        log_err(f"Go not found — cannot install {name}. Install Go from https://go.dev/dl/")
        return
    log_info(f"Installing {name} via go install …")
    os.system(f"go install {repo}@latest")
    # go installs to ~/go/bin — add to PATH for this process
    go_bin = str(Path.home() / "go" / "bin")
    if go_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + go_bin

def _apt_install(pkgs: list):
    """Install system packages; skip gracefully if apt not available."""
    if not shutil.which("apt"):
        log_warn("apt not found — skipping system package install. Install manually: " + ", ".join(pkgs))
        return
    pkgs_str = " ".join(pkgs)
    log_info(f"apt install: {pkgs_str}")
    os.system(f"sudo apt-get install -y -qq {pkgs_str}")

def _pip_install_tool(pkg: str):
    """Install a Python CLI tool (like arjun) via pip --user."""
    cmd = [sys.executable, "-m", "pip", "install", "--user", "--quiet", pkg]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "externally-managed" in result.stderr:
        cmd += ["--break-system-packages"]
        subprocess.run(cmd, check=False)


def setup_tools():
    print(Fore.MAGENTA + "\n[TOOL SETUP]")
    go_tools = {
        "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder",
        "httpx":     "github.com/projectdiscovery/httpx/cmd/httpx",
        "katana":    "github.com/projectdiscovery/katana/cmd/katana",
        "nuclei":    "github.com/projectdiscovery/nuclei/v3/cmd/nuclei",
        "ffuf":      "github.com/ffuf/ffuf/v2",
        "dalfox":    "github.com/hahwul/dalfox/v2",
        "gau":       "github.com/lc/gau/v2/cmd/gau",
        "anew":      "github.com/tomnomnom/anew",
    }
    for name, repo in go_tools.items():
        _install_go_tool(name, repo)

    _pip_install_tool("arjun")

    _apt_install(["nmap", "whatweb", "wafw00f", "sqlmap", "curl", "git"])
    log_ok("Tool setup complete\n")


# ─────────────────────────────────────────────
#  WORDLIST SETUP
# ─────────────────────────────────────────────
def setup_wordlist():
    path = Path(WORDLIST_DIR) / "PayloadsAllTheThings"
    if not path.exists():
        log_info("Cloning PayloadsAllTheThings wordlist …")
        os.system(f"git clone --quiet https://github.com/swisskyrepo/PayloadsAllTheThings.git {path}")
    else:
        log_ok("Wordlists already present")

    # SecLists subset (common dirs)
    seclists_dir = Path(WORDLIST_DIR) / "SecLists-common"
    if not seclists_dir.exists():
        log_info("Cloning SecLists (common subset) …")
        os.system(
            f"git clone --quiet --depth 1 --filter=blob:none --sparse "
            f"https://github.com/danielmiessler/SecLists.git {seclists_dir}"
        )
        os.system(
            f"cd {seclists_dir} && git sparse-checkout set "
            f"Discovery/Web-Content Fuzzing"
        )
    else:
        log_ok("SecLists already present")


# ─────────────────────────────────────────────
#  RECON
# ─────────────────────────────────────────────
def subdomains(domain: str, rate: int) -> str:
    update_status("Subdomains")
    out = f"{OUTPUT_DIR}/{domain}_subs.txt"
    log_info(f"Subdomain enumeration → {out}")
    run_cmd(f"subfinder -d {domain} -silent -o {out}", rate)

    # Augment with gau passive domains if available
    if shutil.which("gau"):
        tmp = f"{OUTPUT_DIR}/{domain}_gau_domains.txt"
        run_cmd(f"gau --subs {domain} 2>/dev/null | grep -oP '^https?://[^/]+' | sort -u > {tmp}", rate)
        if Path(tmp).exists():
            run_cmd(f"cat {tmp} >> {out} && sort -u -o {out} {out}", rate)

    count = len(safe_read_lines(out))
    log_ok(f"Subdomains found: {count}")
    return out


def alive(subs_file: str, rate: int) -> str:
    update_status("Alive check")
    out = subs_file.replace("_subs.", "_live.")
    log_info(f"Probing live hosts → {out}")
    run_cmd(
        f"httpx -l {subs_file} -rate-limit {rate} -silent "
        f"-title -status-code -tech-detect -o {out}",
        rate,
    )
    count = len(safe_read_lines(out))
    log_ok(f"Live hosts: {count}")
    return out


def crawl(live_file: str, rate: int) -> str:
    update_status("Crawling")
    out = live_file.replace("_live.", "_urls.")
    log_info(f"Crawling URLs → {out}")
    run_cmd(
        f"katana -list {live_file} -rl {rate} -silent "
        f"-js-crawl -passive -o {out}",
        rate,
    )
    count = len(safe_read_lines(out))
    log_ok(f"URLs collected: {count}")
    return out


def extract_params(urls_file: str) -> str:
    update_status("Param extraction")
    out = urls_file.replace("_urls.", "_params.")
    lines = safe_read_lines(urls_file)
    param_urls = [l for l in lines if "=" in l]
    Path(out).write_text("\n".join(param_urls) + "\n")
    log_ok(f"Param URLs: {len(param_urls)}")
    return out


def dir_fuzz(live_file: str, rate: int) -> str:
    """FFUF directory brute-force on each live host."""
    update_status("Dir fuzzing")
    wordlist = (
        Path(WORDLIST_DIR)
        / "SecLists-common"
        / "Discovery"
        / "Web-Content"
        / "common.txt"
    )
    if not wordlist.exists():
        log_warn("SecLists common.txt not found — skipping dir fuzz")
        return ""

    out_dir = f"{OUTPUT_DIR}/ffuf"
    ensure_dirs(out_dir)
    hosts = safe_read_lines(live_file)

    for host in hosts[:20]:   # cap at 20 hosts to avoid runaway
        # strip metadata added by httpx (e.g. "[200] title ...")
        url = host.split()[0]
        safe_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
        out = f"{out_dir}/{safe_name}.json"
        run_cmd(
            f"ffuf -u {url}/FUZZ -w {wordlist} -mc 200,204,301,302,307,403 "
            f"-t 40 -of json -o {out} -s",
            rate,
        )
    log_ok("Dir fuzzing complete")
    return out_dir


# ─────────────────────────────────────────────
#  SCANNING
# ─────────────────────────────────────────────
def nuclei_scan(live_file: str, rate: int) -> str:
    update_status("Nuclei scan")
    out = live_file.replace("_live.", "_nuclei.")
    log_info(f"Nuclei OWASP scan → {out}")
    run_cmd(
        f"nuclei -l {live_file} -severity critical,high,medium "
        f"-rate-limit {rate} -silent -o {out}",
        rate,
    )
    return out


def dalfox_scan(params_file: str, rate: int) -> str:
    update_status("Dalfox XSS")
    out = params_file.replace("_params.", "_dalfox.")
    if not Path(params_file).exists() or not safe_read_lines(params_file):
        log_warn("No param URLs for dalfox — skipping")
        return ""
    log_info(f"Dalfox XSS scan → {out}")
    run_cmd(f"dalfox file {params_file} --silence -o {out}", rate)
    return out


def sqli_scan(params_file: str):
    """Run sqlmap on first 10 param URLs with safe defaults."""
    update_status("SQLi scan")
    urls = safe_read_lines(params_file)[:10]
    if not urls:
        log_warn("No URLs for sqlmap — skipping")
        return
    if not shutil.which("sqlmap"):
        log_warn("sqlmap not found — skipping SQLi scan")
        return
    for url in urls:
        check_pause()
        run_cmd(
            f"sqlmap -u '{url}' --batch --level=1 --risk=1 "
            f"--output-dir={OUTPUT_DIR}/sqlmap --forms --crawl=1 "
            f"--no-cast 2>/dev/null"
        )


# ─────────────────────────────────────────────
#  VULNERABILITY DETECTORS
# ─────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "EngineX/2.0 (Bug Bounty Recon)"})


def _http_get(url: str) -> Optional[requests.Response]:
    try:
        return SESSION.get(url.strip(), timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException:
        return None


def xss_scan(params_file: str) -> str:
    update_status("XSS basic check")
    out = params_file.replace("_params.", "_xss_basic.")
    urls = safe_read_lines(params_file)
    hits = []

    log_info(f"Basic XSS reflection check on {len(urls)} URLs …")
    for url in tqdm(urls, desc="XSS", unit="url", ncols=80):
        check_pause()
        # Inject marker into every param value
        test_url = ""
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(url)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            for key in qs:
                qs[key] = ["RAVXSS"]
            new_query = urlencode(qs, doseq=True)
            test_url = urlunparse(parsed._replace(query=new_query))
        except Exception:
            test_url = url.split("=")[0] + "=RAVXSS"

        resp = _http_get(test_url)
        if resp and "RAVXSS" in resp.text:
            hits.append(test_url)

    Path(out).write_text("\n".join(hits) + "\n")
    log_ok(f"Potential XSS reflections: {len(hits)}")
    return out


def ssrf_scan(params_file: str) -> str:
    update_status("SSRF check")
    out = params_file.replace("_params.", "_ssrf.")
    keys = {"url", "redirect", "dest", "destination", "next", "target", "path",
            "uri", "callback", "return", "redir", "r", "link", "goto", "host"}
    urls = safe_read_lines(params_file)
    hits = [u for u in urls if any(k + "=" in u.lower() for k in keys)]
    Path(out).write_text("\n".join(hits) + "\n")
    log_ok(f"Potential SSRF candidates: {len(hits)}")
    return out


def idor_scan(params_file: str) -> str:
    update_status("IDOR check")
    out = params_file.replace("_params.", "_idor.")
    keys = {"id", "user", "uid", "account", "profile", "order", "invoice",
            "customer", "member", "record", "num", "no"}
    urls = safe_read_lines(params_file)
    hits = [u for u in urls if any(k + "=" in u.lower() for k in keys)]
    Path(out).write_text("\n".join(hits) + "\n")
    log_ok(f"Potential IDOR candidates: {len(hits)}")
    return out


def open_redirect_scan(params_file: str) -> str:
    update_status("Open redirect check")
    out = params_file.replace("_params.", "_redirect.")
    keys = {"redirect", "next", "return", "redir", "r", "goto", "url",
            "continue", "forward", "dest"}
    urls = safe_read_lines(params_file)
    hits = []
    for url in urls:
        lower = url.lower()
        if not any(k + "=" in lower for k in keys):
            continue
        # Quick check: does injecting http://evil.com cause a redirect?
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(url)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            for key in list(qs.keys()):
                if key.lower() in keys:
                    qs[key] = ["https://evil.com"]
            test_url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
            resp = _http_get(test_url)
            if resp and "evil.com" in resp.url:
                hits.append(test_url)
        except Exception:
            hits.append(url)   # flag for manual review

    Path(out).write_text("\n".join(hits) + "\n")
    log_ok(f"Open redirect candidates: {len(hits)}")
    return out


def lfi_scan(params_file: str) -> str:
    """Lightweight LFI detection via path traversal payloads."""
    update_status("LFI check")
    out = params_file.replace("_params.", "_lfi.")
    payloads = ["../../../../etc/passwd", "..%2f..%2f..%2fetc/passwd", "%2e%2e/%2e%2e/etc/passwd"]
    keys = {"file", "path", "page", "template", "dir", "include", "inc", "view", "doc", "load"}
    urls = safe_read_lines(params_file)
    hits = []
    for url in tqdm(urls, desc="LFI", unit="url", ncols=80):
        lower = url.lower()
        if not any(k + "=" in lower for k in keys):
            continue
        check_pause()
        for pl in payloads:
            try:
                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                parsed = urlparse(url)
                qs = parse_qs(parsed.query, keep_blank_values=True)
                for key in list(qs.keys()):
                    if key.lower() in keys:
                        qs[key] = [pl]
                test_url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
                resp = _http_get(test_url)
                if resp and "root:" in resp.text:
                    hits.append(test_url)
                    break
            except Exception:
                pass
    Path(out).write_text("\n".join(hits) + "\n")
    log_ok(f"Potential LFI hits: {len(hits)}")
    return out


# ─────────────────────────────────────────────
#  RESULT CLASSIFIER
# ─────────────────────────────────────────────
VULN_KEYWORDS = {
    "xss":  ["xss", "cross-site", "script"],
    "sqli": ["sql", "injection", "mysql", "sqlite", "postgresql"],
    "ssrf": ["ssrf", "server-side request"],
    "lfi":  ["lfi", "local file", "path traversal", "directory traversal"],
    "rce":  ["rce", "remote code", "command injection", "exec"],
    "ssti": ["ssti", "template injection", "jinja", "twig"],
    "idor": ["idor", "insecure direct"],
}

def classify(nuclei_file: str):
    if not Path(nuclei_file).exists():
        return
    lines = safe_read_lines(nuclei_file)
    cats = {k: [] for k in VULN_KEYWORDS}
    for line in lines:
        low = line.lower()
        for cat, kws in VULN_KEYWORDS.items():
            if any(kw in low for kw in kws):
                cats[cat].append(line)
                break
    for cat, findings in cats.items():
        if findings:
            fpath = f"{OUTPUT_DIR}/classified_{cat}.txt"
            Path(fpath).write_text("\n".join(findings) + "\n")
            log_ok(f"  {cat.upper()}: {len(findings)} finding(s) → {fpath}")


# ─────────────────────────────────────────────
#  REPORT GENERATOR
# ─────────────────────────────────────────────
def generate_report(domain: str, artifacts: dict) -> str:
    """Write a structured JSON report + a human-readable Markdown summary."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_report = f"{OUTPUT_DIR}/{domain}_{ts}_report.json"
    md_report   = f"{OUTPUT_DIR}/{domain}_{ts}_report.md"

    # Count findings per category
    summary = {}
    for key, filepath in artifacts.items():
        if filepath and Path(filepath).exists():
            summary[key] = len(safe_read_lines(filepath))
        else:
            summary[key] = 0

    full = {
        "meta": {
            "tool": "EngineX v2.0",
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
        },
        "artifacts": artifacts,
        "summary": summary,
    }
    Path(json_report).write_text(json.dumps(full, indent=2))

    # Markdown
    md_lines = [
        f"# EngineX v2.0 Report — {domain}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "| Category | Count |",
        "|----------|-------|",
    ]
    for k, v in summary.items():
        md_lines.append(f"| {k} | {v} |")

    md_lines += [
        "",
        "## Artifact Paths",
    ]
    for k, v in artifacts.items():
        md_lines.append(f"- **{k}**: `{v}`")

    Path(md_report).write_text("\n".join(md_lines) + "\n")

    log_ok(f"JSON report  → {json_report}")
    log_ok(f"MD  report   → {md_report}")
    return json_report


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="EngineX v2.0 — Automated Bug Bounty Recon Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-d", "--domain",    required=True, help="Target domain (e.g. example.com)")
    parser.add_argument("-r", "--rate",      type=int, default=DEFAULT_RATE, help="Requests per second (default: 50)")
    parser.add_argument("--skip-install",    action="store_true", help="Skip tool installation")
    parser.add_argument("--skip-wordlists",  action="store_true", help="Skip wordlist download")
    parser.add_argument("--no-fuzz",         action="store_true", help="Skip FFUF directory fuzzing")
    parser.add_argument("--no-sqli",         action="store_true", help="Skip sqlmap scan")
    parser.add_argument("--bg",              action="store_true", help="Run in background with nohup")
    args = parser.parse_args()

    # ── Background mode ──────────────────────────────────────────────
    if args.bg:
        cmd = ["nohup", sys.executable, __file__] + [
            a for a in sys.argv[1:] if a != "--bg"
        ]
        subprocess.Popen(cmd, stdout=open("enginex_bg.log", "w"), stderr=subprocess.STDOUT)
        print(f"[*] EngineX launched in background. Logs → enginex_bg.log")
        sys.exit(0)

    # ── Bootstrap ────────────────────────────────────────────────────
    banner()
    ensure_dirs(OUTPUT_DIR, WORDLIST_DIR)

    if not args.skip_install:
        setup_tools()
    if not args.skip_wordlists:
        setup_wordlist()

    rate = args.rate
    domain = args.domain

    log_info(f"Target: {domain}  |  Rate: {rate} req/s\n")

    # ── Recon ─────────────────────────────────────────────────────────
    subs_file   = subdomains(domain, rate)
    live_file   = alive(subs_file, rate)
    urls_file   = crawl(live_file, rate)
    params_file = extract_params(urls_file)

    if not args.no_fuzz:
        dir_fuzz(live_file, rate)

    # ── Scanning ──────────────────────────────────────────────────────
    nuclei_file  = nuclei_scan(live_file, rate)
    dalfox_file  = dalfox_scan(params_file, rate)

    if not args.no_sqli:
        sqli_scan(params_file)

    # ── Detectors ─────────────────────────────────────────────────────
    xss_file      = xss_scan(params_file)
    ssrf_file     = ssrf_scan(params_file)
    idor_file     = idor_scan(params_file)
    redirect_file = open_redirect_scan(params_file)
    lfi_file      = lfi_scan(params_file)

    # ── Classify & Report ─────────────────────────────────────────────
    classify(nuclei_file)

    artifacts = {
        "subdomains":    subs_file,
        "live_hosts":    live_file,
        "urls":          urls_file,
        "params":        params_file,
        "nuclei":        nuclei_file,
        "dalfox_xss":    dalfox_file,
        "xss_basic":     xss_file,
        "ssrf":          ssrf_file,
        "idor":          idor_file,
        "open_redirect": redirect_file,
        "lfi":           lfi_file,
    }

    generate_report(domain, artifacts)

    print(Fore.GREEN + Style.BRIGHT + "\n🔥 EngineX v2.0 — Scan Complete!\n")


if __name__ == "__main__":
    main()
