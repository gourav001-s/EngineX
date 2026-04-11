#!/usr/bin/env python3
"""
███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗  ██╗
██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝╚██╗██╔╝
█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗   ╚███╔╝
██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝   ██╔██╗
███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗██╔╝ ██╗
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

        ⚡ EngineX v3.0 — Automated Bug Bounty Recon Framework ⚡
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

# ══════════════════════════════════════════════════════════
#  DEPENDENCY BOOTSTRAP  (runs before any third-party import)
# ══════════════════════════════════════════════════════════
def _bootstrap():
    required = {
        "requests":  "requests",
        "colorama":  "colorama",
        "tqdm":      "tqdm",
        "reportlab": "reportlab",
    }
    missing = []
    for imp, pkg in required.items():
        try:
            __import__(imp)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    print(f"[*] Auto-installing missing packages: {', '.join(missing)}")
    base = [sys.executable, "-m", "pip", "install", "--user", "--quiet"]
    for pkg in missing:
        r = subprocess.run(base + [pkg], capture_output=True, text=True)
        if r.returncode != 0:
            if "externally-managed" in r.stderr:
                r2 = subprocess.run(
                    base + ["--break-system-packages", pkg],
                    capture_output=True, text=True
                )
                if r2.returncode != 0:
                    print(f"[ERROR] Cannot install {pkg}:\n{r2.stderr.strip()}")
                    sys.exit(1)
            else:
                print(f"[ERROR] Cannot install {pkg}:\n{r.stderr.strip()}")
                sys.exit(1)

    import importlib, site
    importlib.invalidate_caches()
    usite = site.getusersitepackages()
    if usite not in sys.path:
        sys.path.insert(0, usite)
    print("[+] All dependencies ready.\n")

_bootstrap()

# ══════════════════════════════════════════════════════════
#  THIRD-PARTY IMPORTS  (safe after bootstrap)
# ══════════════════════════════════════════════════════════
import requests
from colorama import Fore, Style, init
from tqdm import tqdm

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER

init(autoreset=True)

# ══════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════
BASE_DIR     = Path("EngineX")
DEFAULT_RATE = 50
TIMEOUT      = 8
PAUSE_FILE   = "pause.flag"


# ══════════════════════════════════════════════════════════
#  WORKSPACE  ─  EngineX/<target>/
# ══════════════════════════════════════════════════════════
class Workspace:
    """
    All output goes into:
        EngineX/
        └── <domain>/
            ├── subfinder.txt      subdomains
            ├── gau.txt            passive URLs
            ├── httpx.txt          live hosts
            ├── katana.txt         crawled URLs
            ├── params.txt         parameter URLs
            ├── nuclei.txt         nuclei findings
            ├── dalfox.txt         XSS (dalfox)
            ├── xss.txt            XSS (reflection)
            ├── ssrf.txt           SSRF candidates
            ├── idor.txt           IDOR candidates
            ├── lfi.txt            LFI hits
            ├── redirect.txt       open redirect
            ├── classified_*.txt   classified nuclei
            ├── ffuf/              per-host dir fuzz
            ├── sqlmap/            sqlmap output
            ├── enginex.log        full execution log
            ├── status.txt         current phase
            └── reports/
                ├── report.json
                ├── report.html
                └── report.pdf
    """
    def __init__(self, domain: str):
        self.domain      = domain
        self.root        = BASE_DIR / domain
        self.reports_dir = self.root / "reports"
        self.ffuf_dir    = self.root / "ffuf"
        self.sqlmap_dir  = self.root / "sqlmap"
        self.wl_dir      = BASE_DIR / "wordlists"
        self._mkdirs()
        self._init_log()

    def _mkdirs(self):
        for d in [self.root, self.reports_dir, self.ffuf_dir,
                  self.sqlmap_dir, self.wl_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _init_log(self):
        log_path = self.root / "enginex.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s  %(message)s",
            datefmt="%H:%M:%S",
            handlers=[
                logging.FileHandler(log_path, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.status_file = self.root / "status.txt"

    # ── helpers ───────────────────────────────────────────
    def f(self, name: str) -> str:
        """Absolute path string for a named output file inside root."""
        return str(self.root / name)

    def set_status(self, s: str):
        self.status_file.write_text(s)

    def info(self, m): logging.info(Fore.CYAN   + m)
    def ok  (self, m): logging.info(Fore.GREEN  + "[+] " + m)
    def warn(self, m): logging.warning(Fore.YELLOW + "[!] " + m)
    def err (self, m): logging.error(Fore.RED   + "[x] " + m)


# ══════════════════════════════════════════════════════════
#  MISC UTILITIES
# ══════════════════════════════════════════════════════════
def _sig(sig, frame):
    print(f"\n{Fore.YELLOW}[!] Interrupted. Partial results saved.")
    sys.exit(0)

signal.signal(signal.SIGINT, _sig)


def safe_lines(fp: str) -> list:
    p = Path(fp)
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text(errors="ignore").splitlines() if l.strip()]


def run_cmd(cmd: str, ws: Workspace, rate: int = DEFAULT_RATE) -> int:
    ws.info(f"CMD → {cmd}")
    ret = os.system(cmd)
    if ret != 0:
        ws.warn(f"Exit code {ret}")
    time.sleep(1 / max(rate, 1))
    return ret


def check_pause():
    while Path(PAUSE_FILE).exists():
        print(Fore.YELLOW + "[||] PAUSED — delete pause.flag to continue")
        time.sleep(5)


# ══════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════
def banner():
    print(Fore.CYAN + Style.BRIGHT + r"""
███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗  ██╗
██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝╚██╗██╔╝
█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗   ╚███╔╝
██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝   ██╔██╗
███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗██╔╝ ██╗
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
""")
    print(Fore.GREEN  + Style.BRIGHT + "        ⚡ EngineX v3.0 — Bug Bounty Recon Framework ⚡")
    print(Fore.WHITE  + "                       Developed by RAVX\n")
    print(Fore.YELLOW + f"  [OS]     {platform.system()} {platform.release()} | {platform.machine()}")
    print(Fore.YELLOW + f"  [Python] {platform.python_version()}")
    print(Fore.YELLOW + f"  [Time]   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


# ══════════════════════════════════════════════════════════
#  TOOL SETUP
# ══════════════════════════════════════════════════════════
def _go_in_path():
    gb = str(Path.home() / "go" / "bin")
    if gb not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + gb

def _go_tool(name: str, repo: str, ws: Workspace):
    _go_in_path()
    if shutil.which(name):
        ws.ok(f"{name} already installed")
        return
    if not shutil.which("go"):
        ws.warn(f"Go not found — skipping {name}. Install: https://go.dev/dl/")
        return
    ws.info(f"Installing {name} …")
    os.system(f"go install {repo}@latest")

def _apt(pkgs: list, ws: Workspace):
    if not shutil.which("apt-get"):
        ws.warn("apt not available — install manually: " + " ".join(pkgs))
        return
    os.system(f"sudo apt-get install -y -qq {' '.join(pkgs)} 2>/dev/null")

def _pip(pkg: str):
    base = [sys.executable, "-m", "pip", "install", "--user", "--quiet", pkg]
    r = subprocess.run(base, capture_output=True, text=True)
    if r.returncode != 0 and "externally-managed" in r.stderr:
        subprocess.run(base + ["--break-system-packages"], check=False)

def setup_tools(ws: Workspace):
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
        _go_tool(name, repo, ws)
    _pip("arjun")
    _apt(["nmap","whatweb","wafw00f","sqlmap","curl","git"], ws)
    ws.ok("Tool setup complete\n")


def setup_wordlists(ws: Workspace):
    pat = ws.wl_dir / "PayloadsAllTheThings"
    if not pat.exists():
        ws.info("Cloning PayloadsAllTheThings …")
        os.system(f"git clone --quiet https://github.com/swisskyrepo/PayloadsAllTheThings.git {pat}")
    else:
        ws.ok("PayloadsAllTheThings already present")

    sl = ws.wl_dir / "SecLists-common"
    if not sl.exists():
        ws.info("Cloning SecLists (sparse checkout) …")
        os.system(
            f"git clone --quiet --depth 1 --filter=blob:none --sparse "
            f"https://github.com/danielmiessler/SecLists.git {sl}"
        )
        os.system(f"cd {sl} && git sparse-checkout set Discovery/Web-Content Fuzzing")
    else:
        ws.ok("SecLists already present")


# ══════════════════════════════════════════════════════════
#  RECON PHASE
# ══════════════════════════════════════════════════════════
def run_subfinder(ws: Workspace, rate: int) -> str:
    ws.set_status("subfinder")
    out = ws.f("subfinder.txt")
    ws.info("Running subfinder …")
    run_cmd(f"subfinder -d {ws.domain} -silent -o {out}", ws, rate)

    if shutil.which("gau"):
        tmp = ws.f("gau.txt")
        run_cmd(
            f"gau --subs {ws.domain} 2>/dev/null "
            f"| grep -oP '^https?://[^/]+' | sed 's|https://||;s|http://||' "
            f"| sort -u > {tmp}",
            ws, rate
        )
        if Path(tmp).exists() and safe_lines(tmp):
            run_cmd(f"cat {tmp} >> {out} && sort -u -o {out} {out}", ws, rate)

    n = len(safe_lines(out))
    ws.ok(f"subfinder.txt — {n} subdomains")
    return out


def run_httpx(ws: Workspace, subs: str, rate: int) -> str:
    ws.set_status("httpx")
    out = ws.f("httpx.txt")
    ws.info("Running httpx …")
    run_cmd(
        f"httpx -l {subs} -rate-limit {rate} -silent "
        f"-title -status-code -tech-detect -o {out}",
        ws, rate
    )
    ws.ok(f"httpx.txt — {len(safe_lines(out))} live hosts")
    return out


def run_katana(ws: Workspace, live: str, rate: int) -> str:
    ws.set_status("katana")
    out = ws.f("katana.txt")
    ws.info("Running katana …")
    run_cmd(
        f"katana -list {live} -rl {rate} -silent "
        f"-js-crawl -passive -o {out}",
        ws, rate
    )
    ws.ok(f"katana.txt — {len(safe_lines(out))} URLs")
    return out


def extract_params(ws: Workspace, urls: str) -> str:
    ws.set_status("param extraction")
    out = ws.f("params.txt")
    lines = safe_lines(urls)
    hits = [l for l in lines if "=" in l]
    Path(out).write_text("\n".join(hits) + "\n")
    ws.ok(f"params.txt — {len(hits)} parameter URLs")
    return out


def run_ffuf(ws: Workspace, live: str, rate: int):
    ws.set_status("ffuf")
    wl = ws.wl_dir / "SecLists-common" / "Discovery" / "Web-Content" / "common.txt"
    if not wl.exists():
        ws.warn("SecLists common.txt not found — skipping ffuf")
        return
    hosts = safe_lines(live)
    ws.info(f"Running ffuf on {min(len(hosts),20)} hosts …")
    for h in hosts[:20]:
        url  = h.split()[0]
        name = url.replace("https://","").replace("http://","").replace("/","_")
        out  = str(ws.ffuf_dir / f"{name}.json")
        run_cmd(
            f"ffuf -u {url}/FUZZ -w {wl} "
            f"-mc 200,204,301,302,307,403 -t 40 -of json -o {out} -s",
            ws, rate
        )
    ws.ok("ffuf complete — results in ffuf/")


# ══════════════════════════════════════════════════════════
#  SCANNING PHASE
# ══════════════════════════════════════════════════════════
def run_nuclei(ws: Workspace, live: str, rate: int) -> str:
    ws.set_status("nuclei")
    out = ws.f("nuclei.txt")
    ws.info("Running nuclei …")
    run_cmd(
        f"nuclei -l {live} -severity critical,high,medium "
        f"-rate-limit {rate} -silent -o {out}",
        ws, rate
    )
    ws.ok(f"nuclei.txt — {len(safe_lines(out))} findings")
    return out


def run_dalfox(ws: Workspace, params: str, rate: int) -> str:
    ws.set_status("dalfox")
    out = ws.f("dalfox.txt")
    if not safe_lines(params):
        ws.warn("No param URLs — skipping dalfox")
        return ""
    ws.info("Running dalfox …")
    run_cmd(f"dalfox file {params} --silence -o {out}", ws, rate)
    ws.ok(f"dalfox.txt — {len(safe_lines(out))} XSS hits")
    return out


def run_sqlmap(ws: Workspace, params: str):
    ws.set_status("sqlmap")
    if not shutil.which("sqlmap"):
        ws.warn("sqlmap not found — skipping")
        return
    urls = safe_lines(params)[:10]
    if not urls:
        ws.warn("No param URLs — skipping sqlmap")
        return
    ws.info(f"Running sqlmap on {len(urls)} URLs …")
    for url in urls:
        check_pause()
        run_cmd(
            f"sqlmap -u '{url}' --batch --level=1 --risk=1 "
            f"--output-dir={ws.sqlmap_dir} --forms --crawl=1 --no-cast 2>/dev/null",
            ws
        )
    ws.ok("sqlmap complete — results in sqlmap/")


# ══════════════════════════════════════════════════════════
#  VULNERABILITY DETECTORS
# ══════════════════════════════════════════════════════════
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "EngineX/3.0 (Bug Bounty Recon)"})


def _get(url: str) -> Optional[requests.Response]:
    try:
        return _SESSION.get(url.strip(), timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException:
        return None


def _inject(url: str, value: str) -> str:
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    try:
        p  = urlparse(url)
        qs = parse_qs(p.query, keep_blank_values=True)
        for k in qs:
            qs[k] = [value]
        return urlunparse(p._replace(query=urlencode(qs, doseq=True)))
    except Exception:
        return url.split("=")[0] + "=" + value


def run_xss(ws: Workspace, params: str) -> str:
    ws.set_status("xss")
    out  = ws.f("xss.txt")
    urls = safe_lines(params)
    hits = []
    ws.info(f"XSS reflection scan on {len(urls)} URLs …")
    for url in tqdm(urls, desc="XSS", unit="url", ncols=80):
        check_pause()
        r = _get(_inject(url, "RAVXSS"))
        if r and "RAVXSS" in r.text:
            hits.append(_inject(url, "RAVXSS"))
    Path(out).write_text("\n".join(hits) + "\n")
    ws.ok(f"xss.txt — {len(hits)} reflection hits")
    return out


def run_ssrf(ws: Workspace, params: str) -> str:
    ws.set_status("ssrf")
    out  = ws.f("ssrf.txt")
    keys = {"url","redirect","dest","destination","next","target","path",
            "uri","callback","return","redir","r","link","goto","host","fetch"}
    urls = safe_lines(params)
    hits = [u for u in urls if any(k+"=" in u.lower() for k in keys)]
    Path(out).write_text("\n".join(hits) + "\n")
    ws.ok(f"ssrf.txt — {len(hits)} candidates")
    return out


def run_idor(ws: Workspace, params: str) -> str:
    ws.set_status("idor")
    out  = ws.f("idor.txt")
    keys = {"id","user","uid","account","profile","order","invoice",
            "customer","member","record","num","no","pid","userid","docid"}
    urls = safe_lines(params)
    hits = [u for u in urls if any(k+"=" in u.lower() for k in keys)]
    Path(out).write_text("\n".join(hits) + "\n")
    ws.ok(f"idor.txt — {len(hits)} candidates")
    return out


def run_lfi(ws: Workspace, params: str) -> str:
    ws.set_status("lfi")
    out      = ws.f("lfi.txt")
    payloads = ["../../../../etc/passwd", "..%2f..%2f..%2fetc/passwd",
                "%2e%2e/%2e%2e/etc/passwd", "....//....//etc/passwd"]
    keys     = {"file","path","page","template","dir","include","inc",
                "view","doc","load","read","document","folder","root"}
    urls     = safe_lines(params)
    hits     = []
    for url in tqdm(urls, desc="LFI", unit="url", ncols=80):
        if not any(k+"=" in url.lower() for k in keys):
            continue
        check_pause()
        for pl in payloads:
            r = _get(_inject(url, pl))
            if r and "root:" in r.text:
                hits.append(_inject(url, pl))
                break
    Path(out).write_text("\n".join(hits) + "\n")
    ws.ok(f"lfi.txt — {len(hits)} confirmed hits")
    return out


def run_redirect(ws: Workspace, params: str) -> str:
    ws.set_status("redirect")
    out  = ws.f("redirect.txt")
    keys = {"redirect","next","return","redir","r","goto","url",
            "continue","forward","dest","location","back"}
    urls = safe_lines(params)
    hits = []
    for url in urls:
        if not any(k+"=" in url.lower() for k in keys):
            continue
        check_pause()
        try:
            test = _inject(url, "https://evil.com")
            r    = _get(test)
            if r and "evil.com" in r.url:
                hits.append(test)
            else:
                hits.append(url)
        except Exception:
            hits.append(url)
    Path(out).write_text("\n".join(hits) + "\n")
    ws.ok(f"redirect.txt — {len(hits)} candidates")
    return out


# ══════════════════════════════════════════════════════════
#  CLASSIFIER
# ══════════════════════════════════════════════════════════
VULN_KW = {
    "xss":  ["xss","cross-site","script"],
    "sqli": ["sql","injection","mysql","sqlite","postgresql"],
    "ssrf": ["ssrf","server-side request"],
    "lfi":  ["lfi","local file","path traversal","directory traversal"],
    "rce":  ["rce","remote code","command injection","exec"],
    "ssti": ["ssti","template injection","jinja","twig"],
    "idor": ["idor","insecure direct"],
}

def classify(ws: Workspace, nuclei_file: str):
    if not Path(nuclei_file).exists():
        return
    lines = safe_lines(nuclei_file)
    cats  = {k: [] for k in VULN_KW}
    for line in lines:
        low = line.lower()
        for cat, kws in VULN_KW.items():
            if any(kw in low for kw in kws):
                cats[cat].append(line)
                break
    for cat, findings in cats.items():
        if findings:
            fp = ws.f(f"classified_{cat}.txt")
            Path(fp).write_text("\n".join(findings) + "\n")
            ws.ok(f"classified_{cat}.txt — {len(findings)} finding(s)")


# ══════════════════════════════════════════════════════════
#  COLLECT STATS
# ══════════════════════════════════════════════════════════
def _stats(ws: Workspace, artifacts: dict) -> dict:
    return {
        k: len(safe_lines(fp)) if fp and Path(fp).exists() else 0
        for k, fp in artifacts.items()
    }


# ══════════════════════════════════════════════════════════
#  REPORT — JSON
# ══════════════════════════════════════════════════════════
def write_json(ws: Workspace, artifacts: dict, stats: dict) -> str:
    out = str(ws.reports_dir / "report.json")
    Path(out).write_text(json.dumps({
        "meta": {
            "tool":      "EngineX v3.0",
            "domain":    ws.domain,
            "timestamp": datetime.now().isoformat(),
            "system":    f"{platform.system()} {platform.release()}",
        },
        "summary":   stats,
        "artifacts": artifacts,
    }, indent=2))
    ws.ok(f"report.json  → {out}")
    return out


# ══════════════════════════════════════════════════════════
#  REPORT — HTML
# ══════════════════════════════════════════════════════════
def write_html(ws: Workspace, artifacts: dict, stats: dict) -> str:
    out = str(ws.reports_dir / "report.html")
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = ""
    for key, count in stats.items():
        col = ("#2ecc71" if count == 0 else
               "#e74c3c" if count > 5 else "#f39c12")
        rows += (f"<tr><td>{key.replace('_',' ').title()}</td>"
                 f"<td><span class='badge' style='background:{col}'>{count}</span></td>"
                 f"<td>{artifacts.get(key,'—')}</td></tr>")

    sections = ""
    for key, fp in artifacts.items():
        if not fp or not Path(fp).exists():
            continue
        lines = safe_lines(fp)
        if not lines:
            continue
        items = "".join(
            f"<li><code>{l.replace('&','&amp;').replace('<','&lt;')}</code></li>"
            for l in lines[:100]
        )
        note = (f"<p class='note'>Showing first 100 of {len(lines)} results.</p>"
                if len(lines) > 100 else "")
        sections += (f"<div class='section'>"
                     f"<h2>&#128196; {key.replace('_',' ').title()}</h2>"
                     f"{note}<ul>{items}</ul></div>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>EngineX v3.0 &mdash; {ws.domain}</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--border:#30363d;--accent:#58a6ff;
      --text:#c9d1d9;--muted:#8b949e;}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:var(--bg);color:var(--text);padding:2rem}}
h1{{font-size:2rem;color:var(--accent);margin-bottom:.3rem}}
h2{{font-size:1.15rem;color:var(--accent);margin-bottom:.8rem}}
.meta{{color:var(--muted);font-size:.85rem;margin-bottom:2rem}}
.card,.section{{background:var(--card);border:1px solid var(--border);
               border-radius:8px;padding:1.5rem;margin-bottom:1.5rem}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:.55rem 1rem;border-bottom:1px solid var(--border);
       text-align:left;font-size:.88rem}}
th{{color:var(--muted);font-weight:600}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;
        color:#fff;font-weight:700;font-size:.78rem}}
ul{{list-style:none;padding:0}}
li{{padding:3px 0;border-bottom:1px solid var(--border);font-size:.8rem}}
code{{color:#79c0ff;font-family:monospace;word-break:break-all}}
.note{{color:var(--muted);font-size:.78rem;margin-bottom:.7rem}}
.banner{{font-family:monospace;color:#58a6ff;font-size:.5rem;
         line-height:1.2;margin-bottom:1.5rem;white-space:pre}}
.footer{{text-align:center;color:var(--muted);font-size:.78rem}}
</style>
</head>
<body>
<div class="banner">
&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2563;&#x2588;&#x2588;&#x2588;&#x2557;   &#x2588;&#x2588;&#x2557; &#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2557; &#x2588;&#x2588;&#x2557;&#x2588;&#x2588;&#x2588;&#x2557;   &#x2588;&#x2588;&#x2557;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2563;&#x2588;&#x2588;&#x2557;  &#x2588;&#x2588;&#x2557;
&#x2588;&#x2588;&#x2554;&#x2550;&#x2550;&#x2550;&#x2550;&#x255D;&#x2588;&#x2588;&#x2588;&#x2588;&#x2557;  &#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2554;&#x2550;&#x2550;&#x2550;&#x2550;&#x255D; &#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2588;&#x2588;&#x2557;  &#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2554;&#x2550;&#x2550;&#x2550;&#x2550;&#x255D;&#x255A;&#x2588;&#x2588;&#x2557;&#x2588;&#x2588;&#x2554;&#x255D;
&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2557;  &#x2588;&#x2588;&#x2554;&#x2588;&#x2588;&#x2557; &#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2551;  &#x2588;&#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2554;&#x2588;&#x2588;&#x2557; &#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2557;   &#x255A;&#x2588;&#x2588;&#x2588;&#x2554;&#x255D;
&#x2588;&#x2588;&#x2554;&#x2550;&#x2550;&#x255D;  &#x2588;&#x2588;&#x2551;&#x255A;&#x2588;&#x2588;&#x2557;&#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2551;   &#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2551;&#x255A;&#x2588;&#x2588;&#x2557;&#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2554;&#x2550;&#x2550;&#x255D;   &#x2588;&#x2588;&#x2554;&#x2588;&#x2588;&#x2557;
&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2563;&#x2588;&#x2588;&#x2551; &#x255A;&#x2588;&#x2588;&#x2588;&#x2588;&#x2551;&#x255A;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2554;&#x255D;&#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2551; &#x255A;&#x2588;&#x2588;&#x2588;&#x2588;&#x2551;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x2563;&#x2588;&#x2588;&#x2554;&#x255D; &#x2588;&#x2588;&#x2557;
&#x255A;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x255D;&#x255A;&#x2550;&#x255D;  &#x255A;&#x2550;&#x2550;&#x2550;&#x255D; &#x255A;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x255D; &#x255A;&#x2550;&#x255D;&#x255A;&#x2550;&#x255D;  &#x255A;&#x2550;&#x2550;&#x2550;&#x255D;&#x255A;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x2550;&#x255D;&#x255A;&#x2550;&#x255D;  &#x255A;&#x2550;&#x255D;
</div>
<h1>&#x26A1; EngineX v3.0 &mdash; Scan Report</h1>
<div class="meta">
  <strong>Target:</strong> {ws.domain} &nbsp;|&nbsp;
  <strong>Generated:</strong> {ts} &nbsp;|&nbsp;
  <strong>Tool:</strong> EngineX v3.0 by RAVX
</div>
<div class="card">
  <h2>&#128202; Findings Summary</h2>
  <table>
    <thead><tr><th>Category</th><th>Count</th><th>Output File</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
{sections}
<div class="card footer">
  Generated by <strong>EngineX v3.0</strong> &mdash; Developed by RAVX<br/>
  For authorized security testing only.
</div>
</body></html>"""

    Path(out).write_text(html)
    ws.ok(f"report.html  → {out}")
    return out


# ══════════════════════════════════════════════════════════
#  REPORT — PDF
# ══════════════════════════════════════════════════════════
def write_pdf(ws: Workspace, artifacts: dict, stats: dict) -> str:
    out = str(ws.reports_dir / "report.pdf")
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    DARK   = colors.HexColor("#0d1117")
    CARD   = colors.HexColor("#161b22")
    ACCENT = colors.HexColor("#58a6ff")
    GREEN  = colors.HexColor("#2ecc71")
    RED    = colors.HexColor("#e74c3c")
    YELLOW = colors.HexColor("#f39c12")
    MUTED  = colors.HexColor("#8b949e")
    WHITE  = colors.white
    CODE_C = colors.HexColor("#79c0ff")
    BORDER = colors.HexColor("#30363d")

    doc = SimpleDocTemplate(
        out, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch,  bottomMargin=0.75*inch,
        title=f"EngineX v3.0 — {ws.domain}", author="RAVX"
    )
    styles = getSampleStyleSheet()

    S_TITLE = ParagraphStyle("etitle", fontSize=20, textColor=ACCENT,
                              spaceAfter=4, fontName="Helvetica-Bold")
    S_META  = ParagraphStyle("emeta",  fontSize=9,  textColor=MUTED,
                              spaceAfter=14)
    S_H2    = ParagraphStyle("eh2",    fontSize=12, textColor=ACCENT,
                              spaceBefore=14, spaceAfter=6,
                              fontName="Helvetica-Bold")
    S_CODE  = ParagraphStyle("ecode",  fontSize=7,  textColor=CODE_C,
                              backColor=CARD, leading=10, leftIndent=6,
                              fontName="Courier")
    S_NOTE  = ParagraphStyle("enote",  fontSize=8,  textColor=MUTED,
                              spaceAfter=4)
    S_FOOT  = ParagraphStyle("efoot",  fontSize=7,  textColor=MUTED,
                              alignment=TA_CENTER, spaceBefore=10)

    def dark_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        canvas.restoreState()

    story = []

    story.append(Paragraph("EngineX v3.0 — Scan Report", S_TITLE))
    story.append(Paragraph(
        f"Target: {ws.domain}  |  Generated: {ts}  |  Tool: EngineX v3.0 by RAVX",
        S_META
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=ACCENT, spaceAfter=14))

    # Summary table
    story.append(Paragraph("Findings Summary", S_H2))
    tdata = [["Category", "Count", "Output File"]]
    for key, count in stats.items():
        c = RED if count > 5 else (YELLOW if count > 0 else GREEN)
        tdata.append([
            key.replace("_"," ").title(),
            str(count),
            str(artifacts.get(key,"—"))[:55]
        ])
    tbl = Table(tdata, colWidths=[2.2*inch, 0.8*inch, 4.0*inch], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0),  ACCENT),
        ("TEXTCOLOR",      (0,0), (-1,0),  DARK),
        ("FONTNAME",       (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [DARK, CARD]),
        ("TEXTCOLOR",      (0,1), (-1,-1), WHITE),
        ("GRID",           (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
        ("LEFTPADDING",    (0,0), (-1,-1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 18))

    # Artifact sections
    for key, fp in artifacts.items():
        if not fp or not Path(fp).exists():
            continue
        lines = safe_lines(fp)
        if not lines:
            continue
        story.append(Paragraph(key.replace("_"," ").title(), S_H2))
        story.append(HRFlowable(width="100%", thickness=0.4,
                                color=BORDER, spaceAfter=5))
        if len(lines) > 80:
            story.append(Paragraph(
                f"Showing first 80 of {len(lines)} results — see {fp} for full output.",
                S_NOTE
            ))
        for line in lines[:80]:
            safe = (line.replace("&","&amp;")
                       .replace("<","&lt;")
                       .replace(">","&gt;"))
            story.append(Paragraph(safe, S_CODE))
            story.append(Spacer(1, 1))
        story.append(Spacer(1, 8))

    story.append(HRFlowable(width="100%", thickness=1,
                            color=ACCENT, spaceBefore=8))
    story.append(Paragraph(
        "Generated by EngineX v3.0 — Developed by RAVX | "
        "For authorized security testing only.",
        S_FOOT
    ))

    doc.build(story, onFirstPage=dark_bg, onLaterPages=dark_bg)
    ws.ok(f"report.pdf   → {out}")
    return out


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="EngineX v3.0 — Automated Bug Bounty Recon Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-d","--domain",    required=True,
                        help="Target domain e.g. example.com")
    parser.add_argument("-r","--rate",      type=int, default=DEFAULT_RATE,
                        help="Requests/sec (default 50)")
    parser.add_argument("--skip-install",   action="store_true",
                        help="Skip tool installation")
    parser.add_argument("--skip-wordlists", action="store_true",
                        help="Skip wordlist download")
    parser.add_argument("--no-fuzz",        action="store_true",
                        help="Skip FFUF directory fuzzing")
    parser.add_argument("--no-sqli",        action="store_true",
                        help="Skip sqlmap scan")
    parser.add_argument("--bg",             action="store_true",
                        help="Run in background (nohup)")
    args = parser.parse_args()

    if args.bg:
        BASE_DIR.mkdir(exist_ok=True)
        bg_log = BASE_DIR / f"{args.domain}_bg.log"
        cmd = ["nohup", sys.executable, __file__] + [
            a for a in sys.argv[1:] if a != "--bg"
        ]
        subprocess.Popen(cmd,
                         stdout=open(bg_log, "w"),
                         stderr=subprocess.STDOUT)
        print(f"[*] EngineX running in background — tail -f {bg_log}")
        sys.exit(0)

    banner()

    ws = Workspace(args.domain)
    ws.info(f"Workspace  →  {ws.root.resolve()}")
    ws.info(f"Target: {args.domain}  |  Rate: {args.rate} req/s\n")

    if not args.skip_install:
        setup_tools(ws)
    if not args.skip_wordlists:
        setup_wordlists(ws)

    rate = args.rate

    # ── RECON ──────────────────────────────────────────────
    subs   = run_subfinder(ws, rate)
    live   = run_httpx(ws, subs, rate)
    urls   = run_katana(ws, live, rate)
    params = extract_params(ws, urls)
    if not args.no_fuzz:
        run_ffuf(ws, live, rate)

    # ── SCANNING ───────────────────────────────────────────
    nuclei = run_nuclei(ws, live, rate)
    dalfox = run_dalfox(ws, params, rate)
    if not args.no_sqli:
        run_sqlmap(ws, params)

    # ── DETECTORS ──────────────────────────────────────────
    xss      = run_xss(ws, params)
    ssrf     = run_ssrf(ws, params)
    idor     = run_idor(ws, params)
    lfi      = run_lfi(ws, params)
    redirect = run_redirect(ws, params)

    # ── CLASSIFY ───────────────────────────────────────────
    classify(ws, nuclei)

    # ── REPORTS ────────────────────────────────────────────
    artifacts = {
        "subdomains":    subs,
        "live_hosts":    live,
        "katana_urls":   urls,
        "params":        params,
        "nuclei":        nuclei,
        "dalfox_xss":    dalfox,
        "xss_basic":     xss,
        "ssrf":          ssrf,
        "idor":          idor,
        "lfi":           lfi,
        "open_redirect": redirect,
    }
    stats = _stats(ws, artifacts)

    print(Fore.MAGENTA + "\n[GENERATING REPORTS]")
    json_r = write_json(ws, artifacts, stats)
    html_r = write_html(ws, artifacts, stats)
    pdf_r  = write_pdf(ws, artifacts, stats)

    print(Fore.GREEN + Style.BRIGHT + f"""
╔══════════════════════════════════════════════════════════╗
║         ⚡  EngineX v3.0 — SCAN COMPLETE  ⚡             ║
╠══════════════════════════════════════════════════════════╣
║  Target    : {args.domain:<42} ║
║  Workspace : EngineX/{args.domain:<36} ║
╠══════════════════════════════════════════════════════════╣
║  REPORTS                                                 ║
║  ├─ reports/report.json                                  ║
║  ├─ reports/report.html                                  ║
║  └─ reports/report.pdf                                   ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
