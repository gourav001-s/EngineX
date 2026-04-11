<div align="center">

```
███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗  ██╗
██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝╚██╗██╔╝
█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗   ╚███╔╝ 
██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝   ██╔██╗ 
███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗██╔╝ ██╗
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
```

# ⚡ EngineX v3.0 — Automated Bug Bounty Recon Framework

**Developed by [RAVX](https://github.com/RAVX)**

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Kali%20%7C%20Parrot-informational?style=flat-square&logo=linux)](https://kali.org)
[![License](https://img.shields.io/badge/License-Apache2.0-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.0-red?style=flat-square)]()
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()
[![Reports](https://img.shields.io/badge/Reports-JSON%20%7C%20HTML%20%7C%20PDF-orange?style=flat-square)]()

*A full-pipeline, automated recon and vulnerability discovery framework with structured workspace management and tri-format reporting.*

</div>

---

## 📸 Preview

<!-- Drop your terminal screenshot here -->
<!-- Recommended: take a screenshot of the tool running, save to assets/banner.png -->
<!-- Then replace the block below with: ![EngineX v3.0](assets/banner.png) -->

> <img width="495" height="317" alt="image" src="https://github.com/user-attachments/assets/948e1e12-b085-4ee6-bfce-23f33f64228a" />


---

## 📖 Table of Contents

- [What is EngineX v3.0?](#-what-is-enginex-v30)
- [What's New in v3.0](#-whats-new-in-v30)
- [Features](#-features)
- [Recon Pipeline](#-recon-pipeline)
- [Workspace Structure](#-workspace-structure)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Basic Commands](#basic-commands)
  - [Skip Specific Phases](#skip-specific-phases)
  - [Combined Practical Commands](#combined-practical-commands)
  - [Background Mode](#background-mode)
  - [Pause and Resume](#pause-and-resume-mid-scan)
  - [Accessing Output Files](#accessing-output-files)
  - [Accessing Reports](#accessing-reports)
  - [All Flags Reference](#all-flags-reference)
- [Recommended Bug Bounty Workflow](#-recommended-bug-bounty-workflow)
- [Vulnerability Coverage](#-vulnerability-coverage)
- [Report Formats](#-report-formats)
- [Disclaimer](#-disclaimer)
- [Credits](#-credits)

---

## 🔍 What is EngineX v3.0?

**EngineX v3.0** is a modular, fully automated recon and vulnerability discovery framework built for serious bug bounty hunters and penetration testers. It chains together industry-standard tools into a single-command pipeline that handles everything from subdomain discovery to active exploit checking — and ends every scan with professional tri-format reports.

Every scan creates a clean, isolated workspace under `EngineX/<target>/` where every tool's output is saved as its own named `.txt` file. No more hunting through flat output folders. No more guessing which file holds what data.

> Built for real-world bug bounty hunting. Not a toy scanner.

---

## 🆕 What's New in v3.0

| Change | Details |
|--------|---------|
| **Structured Workspace** | All output inside `EngineX/<target>/` — one isolated folder per target |
| **Named Tool Outputs** | Every tool saves to its own file: `subfinder.txt`, `httpx.txt`, `nuclei.txt`, etc. |
| **HTML Report** | Dark-themed, self-contained HTML report with colour-coded findings table |
| **PDF Report** | ReportLab dark PDF report, auto-generated at scan end |
| **JSON Report** | Machine-readable report with full artifact paths and finding counts |
| **Reports Subfolder** | All three reports saved cleanly in `EngineX/<target>/reports/` |
| **Workspace Class** | Centralized directory management — clean architecture, no scattered path strings |
| **reportlab Bootstrap** | `reportlab` auto-installed like all other deps — no manual install needed |
| **Completion Banner** | Clean scan-end summary showing workspace path and all three report locations |

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🔧 **Auto Dependency Install** | Bootstraps `requests`, `colorama`, `tqdm`, `reportlab` at first run. Handles PEP 668 (Debian/Ubuntu 23+) |
| 📁 **Structured Workspace** | `EngineX/<domain>/` per target — every tool output in its own `.txt` file |
| 🌐 **Subdomain Enumeration** | `subfinder` + `gau` (Wayback, CommonCrawl, OTX) merged for maximum coverage |
| 🟢 **Live Host Detection** | `httpx` with title, status code, and tech-detect |
| 🕷️ **Deep Crawling** | `katana` with JS crawling and passive mode |
| 🔍 **Directory Fuzzing** | `ffuf` + SecLists `common.txt` on up to 20 live hosts |
| 💉 **Nuclei OWASP Scan** | Full nuclei scan filtered to critical/high/medium |
| 🎯 **XSS Detection** | `dalfox` (active) + custom reflection scanner (param-aware URL injection) |
| 🛢️ **SQLi Detection** | `sqlmap` with safe batch defaults on top 10 param URLs |
| 🔁 **SSRF Detection** | 16-keyword parameter pattern matching |
| 🪪 **IDOR Detection** | ID-parameter pattern matching with 15+ key patterns |
| 📂 **LFI Detection** | Path traversal payload injection + `/etc/passwd` response confirmation |
| 🔀 **Open Redirect** | Active injection + final URL verification |
| 🗂️ **Vuln Classifier** | Auto-classifies nuclei output into XSS / SQLi / SSRF / LFI / RCE / SSTI / IDOR files |
| ⏸️ **Pause / Resume** | Flag-file based pause — no scan data lost on pause |
| 🌑 **Background Mode** | nohup background execution with live log tailing |
| 📊 **Tri-Format Reports** | JSON + HTML + PDF auto-generated into `reports/` at scan completion |

---

## 🔄 Recon Pipeline

```
Target Domain
     │
     ▼
[1] Subfinder + GAU ─────────────────  subfinder.txt + gau.txt
     │
     ▼
[2] Live Host Probing ───────────────  httpx.txt
     │
     ▼
[3] URL Crawling ────────────────────  katana.txt
     │
     ▼
[4] Param Extraction ────────────────  params.txt
     │
     ├──▶ [5a] FFUF Dir Fuzzing ─────  ffuf/*.json
     ├──▶ [5b] Nuclei OWASP ─────────  nuclei.txt
     ├──▶ [5c] Dalfox XSS ───────────  dalfox.txt
     ├──▶ [5d] SQLmap ────────────────  sqlmap/
     ├──▶ [5e] XSS Reflection ────────  xss.txt
     ├──▶ [5f] SSRF Candidates ───────  ssrf.txt
     ├──▶ [5g] IDOR Candidates ───────  idor.txt
     ├──▶ [5h] LFI Detection ─────────  lfi.txt
     └──▶ [5i] Open Redirect ─────────  redirect.txt
               │
               ▼
     [6] Classify Nuclei Output ──────  classified_*.txt
               │
               ▼
     [7] Generate Reports
         ├── reports/report.json
         ├── reports/report.html
         └── reports/report.pdf
```

---

## 📁 Workspace Structure

After a scan on `example.com`, this is exactly what gets created:

```
EngineX/
├── wordlists/
│   ├── PayloadsAllTheThings/
│   └── SecLists-common/
│
└── example.com/                    ← isolated folder per target
    │
    ├── subfinder.txt               ← discovered subdomains
    ├── gau.txt                     ← passive URLs from gau
    ├── httpx.txt                   ← live hosts + title + tech stack
    ├── katana.txt                  ← all crawled URLs
    ├── params.txt                  ← URLs with query parameters
    │
    ├── nuclei.txt                  ← nuclei OWASP findings
    ├── dalfox.txt                  ← dalfox XSS hits
    ├── xss.txt                     ← reflection XSS hits
    ├── ssrf.txt                    ← SSRF candidates
    ├── idor.txt                    ← IDOR candidates
    ├── lfi.txt                     ← confirmed LFI hits
    ├── redirect.txt                ← open redirect candidates
    │
    ├── classified_xss.txt
    ├── classified_sqli.txt
    ├── classified_rce.txt
    ├── classified_lfi.txt
    ├── classified_ssrf.txt
    ├── classified_ssti.txt
    ├── classified_idor.txt
    │
    ├── ffuf/                       ← per-host directory fuzz (JSON)
    ├── sqlmap/                     ← sqlmap output directory
    │
    ├── enginex.log                 ← full timestamped execution log
    ├── status.txt                  ← current scan phase (live)
    │
    └── reports/
        ├── report.json             ← machine-readable report
        ├── report.html             ← dark-themed HTML report
        └── report.pdf              ← professional PDF report
```

---

## 📋 Requirements

### System
- **OS:** Linux (Kali Linux, Parrot OS, Ubuntu recommended)
- **Python:** 3.7+
- **Go:** 1.19+ — [download here](https://go.dev/dl/)

### Auto-Installed by EngineX on First Run

**Go Tools:** `subfinder` `httpx` `katana` `nuclei` `ffuf` `dalfox` `gau` `anew`

**Python Packages:** `requests` `colorama` `tqdm` `reportlab` `arjun`

**System (apt):** `nmap` `whatweb` `wafw00f` `sqlmap` `curl` `git`

> If Go is not installed, Go-based tools are skipped with a warning. All other components still run.

---

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/RAVX/enginex.git
cd enginex

# 2. Make executable
chmod +x enginex.py

# 3. Run — all dependencies install automatically
python3 enginex.py -d example.com
```

> No `pip install -r requirements.txt` needed. EngineX handles all of its own dependencies.

**Optional — Add Go binaries to PATH (if not already set):**
```bash
export PATH=$PATH:$HOME/go/bin
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
source ~/.bashrc
```

---

## 🚀 Usage

### Basic Commands

```bash
# Minimal — domain only, all defaults
python3 enginex.py -d example.com

# Custom rate limit (requests per second)
python3 enginex.py -d example.com -r 30

# Aggressive rate (fast VPS / good network)
python3 enginex.py -d example.com -r 100

# Stealth rate (avoid detection / throttled targets)
python3 enginex.py -d example.com -r 10
```

---

### Skip Specific Phases

```bash
# Skip tool installation (already installed)
python3 enginex.py -d example.com --skip-install

# Skip wordlist download (already downloaded)
python3 enginex.py -d example.com --skip-wordlists

# Skip FFUF directory fuzzing
python3 enginex.py -d example.com --no-fuzz

# Skip sqlmap SQLi scan
python3 enginex.py -d example.com --no-sqli

# Skip both install and wordlists (fastest startup on repeat runs)
python3 enginex.py -d example.com --skip-install --skip-wordlists
```

---

### Combined Practical Commands

```bash
# Most common run after first setup
python3 enginex.py -d example.com --skip-install --skip-wordlists -r 50

# Light recon — no fuzzing, no sqlmap
python3 enginex.py -d example.com --no-fuzz --no-sqli --skip-install

# Full scan, stealthy rate, skip install
python3 enginex.py -d example.com --skip-install -r 15

# Full scan from scratch on a new machine
python3 enginex.py -d example.com -r 50
```

---

### Background Mode

```bash
# Run in background (won't stop on terminal close)
python3 enginex.py -d example.com --bg

# Background with custom rate
python3 enginex.py -d example.com -r 40 --bg

# Monitor background scan live
tail -f EngineX/example.com_bg.log

# Check current scan phase
cat EngineX/example.com/status.txt

# View full execution log with timestamps
cat EngineX/example.com/enginex.log
```

---

### Pause and Resume Mid-Scan

```bash
# Pause a running scan
touch pause.flag

# Resume it
rm pause.flag
```

> Scan polls every 5 seconds and continues exactly where it paused. No output is lost.

---

### Accessing Output Files

```bash
# Navigate to target workspace
cd EngineX/example.com/

# View subdomains
cat subfinder.txt

# View live hosts (title + tech stack)
cat httpx.txt

# View all crawled URLs
cat katana.txt

# View parameter URLs (for manual testing)
cat params.txt

# View nuclei findings
cat nuclei.txt

# View dalfox XSS results
cat dalfox.txt

# View XSS reflection hits
cat xss.txt

# View SSRF candidates
cat ssrf.txt

# View IDOR candidates
cat idor.txt

# View confirmed LFI hits
cat lfi.txt

# View open redirect candidates
cat redirect.txt

# View classified vuln categories
cat classified_xss.txt
cat classified_sqli.txt
cat classified_rce.txt
cat classified_lfi.txt
cat classified_ssrf.txt
cat classified_ssti.txt
cat classified_idor.txt

# Count findings across all output files
wc -l *.txt

# Watch scan status live
watch cat status.txt
```

---

### Accessing Reports

```bash
# Navigate to reports folder
cd EngineX/example.com/reports/

# List all generated reports with sizes
ls -lh

# Pretty-print JSON report
python3 -m json.tool report.json

# Open HTML report in default browser
xdg-open report.html

# Open HTML with Firefox specifically
firefox report.html

# Open PDF report
xdg-open report.pdf

# Copy all reports to Desktop
cp EngineX/example.com/reports/* ~/Desktop/
```

---

### All Flags Reference

```bash
python3 enginex.py --help
```

| Flag | Description | Default |
|------|-------------|---------|
| `-d / --domain` | **Required.** Target domain (e.g. `example.com`) | — |
| `-r / --rate` | Requests per second for all tools | `50` |
| `--skip-install` | Skip Go/apt/pip tool installation | Off |
| `--skip-wordlists` | Skip wordlist/SecLists download | Off |
| `--no-fuzz` | Skip FFUF directory fuzzing | Off |
| `--no-sqli` | Skip sqlmap scan | Off |
| `--bg` | Launch in background via nohup | Off |

---

## 🎯 Recommended Bug Bounty Workflow

```bash
# ── Day 1: First time on new machine ──────────────────────────────
# Full setup — installs everything, downloads wordlists, full scan
python3 enginex.py -d target.com -r 30

# ── Day 2+: Tools already installed ───────────────────────────────
python3 enginex.py -d target.com --skip-install --skip-wordlists -r 50

# ── New target on same machine ────────────────────────────────────
# Each target automatically gets its own EngineX/<target>/ folder
python3 enginex.py -d new-target.com --skip-install --skip-wordlists -r 50

# ── Re-run after crash or partial scan ────────────────────────────
python3 enginex.py -d target.com --skip-install --skip-wordlists --no-sqli -r 40

# ── Overnight scan ────────────────────────────────────────────────
python3 enginex.py -d target.com --skip-install --skip-wordlists -r 20 --bg
tail -f EngineX/target.com_bg.log

# ── Check what phase the scan is on right now ─────────────────────
watch cat EngineX/target.com/status.txt

# ── After scan: open all three reports ───────────────────────────
firefox EngineX/target.com/reports/report.html
xdg-open EngineX/target.com/reports/report.pdf
python3 -m json.tool EngineX/target.com/reports/report.json
```

---

## 🛡️ Vulnerability Coverage

| Vulnerability | Detection Method | Tool / Module |
|--------------|-----------------|---------------|
| XSS (Reflected) | Active param injection + marker confirmation | `dalfox` + custom |
| SQL Injection | Active exploitation | `sqlmap` |
| SSRF | 16-keyword parameter pattern matching | Custom detector |
| IDOR | ID-parameter pattern analysis (15+ patterns) | Custom detector |
| LFI / Path Traversal | Payload injection + `root:` response confirmation | Custom detector |
| Open Redirect | Active injection + final URL verification | Custom detector |
| OWASP Top 10 (broad) | Template-based nuclei scan | `nuclei` |
| RCE, SSTI, XXE, etc. | Template-based nuclei scan | `nuclei` |
| Hidden Directories | Brute-force fuzzing | `ffuf` + SecLists |

---

## 📊 Report Formats

### JSON — `reports/report.json`
Machine-readable structured output with scan metadata, per-category finding counts, and absolute artifact file paths. Use this for custom parsers, pipelines, or integrations.

### HTML — `reports/report.html`
Dark-themed, fully self-contained HTML report with:
- Colour-coded findings summary table (green = 0, yellow = low, red = high)
- Full per-category result listings (first 100 results per section)
- Zero external dependencies — works completely offline

### PDF — `reports/report.pdf`
Professional dark-themed PDF built with ReportLab:
- Scan metadata header
- Findings summary table
- Per-category output listings (first 80 results per section)
- Ready to attach directly to bug bounty submissions or pentest reports

---

## ⚠️ Disclaimer

> **EngineX is intended strictly for authorized security testing and educational purposes.**
>
> - Only run EngineX against domains you **own** or have **explicit written permission** to test.
> - Unauthorized scanning is **illegal** under the CFAA, IT Act 2000, and equivalent laws globally.
> - The developer assumes **no liability** for misuse, damage, or legal consequences.
> - Always operate strictly within the scope defined in your bug bounty program's policy.

---

## 🤝 Credits

| Tool | Author | Purpose |
|------|--------|---------|
| [subfinder](https://github.com/projectdiscovery/subfinder) | ProjectDiscovery | Subdomain enumeration |
| [httpx](https://github.com/projectdiscovery/httpx) | ProjectDiscovery | HTTP probing |
| [katana](https://github.com/projectdiscovery/katana) | ProjectDiscovery | Web crawling |
| [nuclei](https://github.com/projectdiscovery/nuclei) | ProjectDiscovery | Template-based scanning |
| [dalfox](https://github.com/hahwul/dalfox) | hahwul | XSS scanning |
| [ffuf](https://github.com/ffuf/ffuf) | ffuf | Directory fuzzing |
| [sqlmap](https://github.com/sqlmapproject/sqlmap) | sqlmapproject | SQL injection |
| [gau](https://github.com/lc/gau) | lc | Passive URL collection |
| [anew](https://github.com/tomnomnom/anew) | tomnomnom | Output deduplication |
| [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | swisskyrepo | Exploit payload wordlists |
| [SecLists](https://github.com/danielmiessler/SecLists) | danielmiessler | Security wordlists |
| [ReportLab](https://www.reportlab.com/) | ReportLab | PDF generation |

---

<div align="center">

**Built with ⚡ by RAVX**

*If EngineX helped you find a bug, drop a ⭐ on the repo*

[![GitHub stars](https://img.shields.io/github/stars/RAVX/enginex?style=social)](https://github.com/RAVX/enginex)

</div>
