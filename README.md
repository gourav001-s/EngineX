<div align="center">

```
███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗  ██╗
██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝╚██╗██╔╝
█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗   ╚███╔╝ 
██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝   ██╔██╗ 
███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗██╔╝ ██╗
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
```

# ⚡ EngineX v2.0 — Automated Bug Bounty Recon Framework

**Developed by [RAVX](https://github.com/RAVX)**

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Kali%20%7C%20Parrot-informational?style=flat-square&logo=linux)](https://kali.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0-red?style=flat-square)]()
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

*A full-pipeline, automated recon and vulnerability discovery framework built for bug bounty hunters.*

</div>

---

## 📸 Preview

<!-- Add your tool banner/screenshot here -->
<!-- Recommended: Take a screenshot of the tool running and place it below -->
<!-- Format: ![EngineX Banner](assets/banner.png) -->

> <img width="516" height="434" alt="Screenshot 2026-04-08 201430" src="https://github.com/user-attachments/assets/7e5948de-6502-4cb4-b8c2-df3b81280568" />




---

## 📖 Table of Contents

- [What is EngineX?](#-what-is-enginex)
- [Features](#-features)
- [Recon Pipeline](#-recon-pipeline)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Basic Commands](#basic-commands)
  - [Skip Flags](#skip-specific-phases)
  - [Combined Commands](#combined-practical-commands)
  - [Background Mode](#background-mode)
  - [Pause & Resume](#pause--resume-mid-scan)
  - [Output & Reports](#output--reports)
  - [All Flags Reference](#all-flags-reference)
- [Recommended Bug Bounty Workflow](#-recommended-bug-bounty-workflow)
- [Output Structure](#-output-structure)
- [Vulnerability Coverage](#-vulnerability-coverage)
- [Disclaimer](#-disclaimer)
- [Credits](#-credits)

---

## 🔍 What is EngineX?

**EngineX** is a modular, fully automated recon and vulnerability discovery framework designed for bug bounty hunters and penetration testers. It chains together industry-standard tools — subfinder, httpx, katana, nuclei, dalfox, ffuf, sqlmap, and more — into a single pipeline that takes a domain and outputs a structured vulnerability report.

From subdomain enumeration to XSS, SQLi, LFI, SSRF, IDOR, and Open Redirect detection, EngineX handles everything with a single command. It also **auto-installs its own dependencies** at first run — no manual setup required.

> Built for real-world bug bounty hunting. Not a toy scanner.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🔧 **Auto Dependency Install** | Installs Go tools, pip packages, apt packages automatically at first run. Handles PEP 668 externally-managed environments (Debian/Ubuntu 23+) |
| 🌐 **Subdomain Enumeration** | subfinder + gau (Wayback, CommonCrawl, OTX) combined for maximum coverage |
| 🟢 **Live Host Detection** | httpx with title, status code, and tech-detect output |
| 🕷️ **Deep Crawling** | katana with JS crawling and passive mode enabled |
| 🔍 **Directory Fuzzing** | ffuf with SecLists common.txt on up to 20 live hosts |
| 💉 **Nuclei OWASP Scan** | Full nuclei scan with critical/high/medium severity filter |
| 🎯 **XSS Detection** | dalfox (active) + custom reflection-based scanner (parameter-aware) |
| 🛢️ **SQLi Detection** | sqlmap with safe batch defaults on param URLs |
| 🔁 **SSRF Detection** | Keyword-based candidate flagging with 15+ parameter patterns |
| 🪪 **IDOR Detection** | Parameter pattern matching for ID-based endpoints |
| 📂 **LFI Detection** | Path traversal payload injection with `/etc/passwd` confirmation |
| 🔀 **Open Redirect** | Active redirect injection with final URL verification |
| ⏸️ **Pause / Resume** | Flag-file based pause system — no scan data lost |
| 🌑 **Background Mode** | nohup-based background execution with live log tailing |
| 📊 **Dual Reports** | JSON (machine-readable) + Markdown (human-readable) reports generated automatically |
| 🗂️ **Vuln Classifier** | Auto-classifies nuclei findings into XSS / SQLi / SSRF / LFI / RCE / SSTI / IDOR categories |

---

## 🔄 Recon Pipeline

```
Target Domain
     │
     ▼
[1] Subdomain Enumeration  ──────  subfinder + gau
     │
     ▼
[2] Live Host Probing  ───────────  httpx (title + tech detect)
     │
     ▼
[3] URL Crawling  ────────────────  katana (JS + passive)
     │
     ▼
[4] Parameter Extraction  ────────  grep '=' filter
     │
     ├──▶ [5a] Directory Fuzzing  ─  ffuf + SecLists
     │
     ├──▶ [5b] Nuclei OWASP Scan  ─  critical/high/medium
     │
     ├──▶ [5c] Dalfox XSS  ─────────  active XSS engine
     │
     ├──▶ [5d] SQLi  ──────────────── sqlmap batch
     │
     ├──▶ [5e] XSS Reflection  ──────  custom param scanner
     │
     ├──▶ [5f] SSRF Candidates  ─────  keyword pattern match
     │
     ├──▶ [5g] IDOR Candidates  ─────  ID param detection
     │
     ├──▶ [5h] LFI Detection  ───────  path traversal payloads
     │
     └──▶ [5i] Open Redirect  ───────  active redirect verify
               │
               ▼
     [6] Classify + Report  ──────── JSON + Markdown
```

---

## 📋 Requirements

### System
- **OS:** Linux (Kali Linux, Parrot OS, Ubuntu recommended)
- **Python:** 3.7+
- **Go:** 1.19+ (for Go-based tools — [download](https://go.dev/dl/))

### Auto-Installed by EngineX
The following are installed automatically on first run:

**Go Tools:** `subfinder`, `httpx`, `katana`, `nuclei`, `ffuf`, `dalfox`, `gau`, `anew`

**Python Packages:** `requests`, `colorama`, `tqdm`, `arjun`

**System (apt):** `nmap`, `whatweb`, `wafw00f`, `sqlmap`, `curl`, `git`

> If Go is not installed, EngineX will skip Go tool installation and warn you. All other tools will still install.

---

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/RAVX/enginex.git
cd enginex

# 2. Make executable
chmod +x enginex.py

# 3. Run — dependencies install automatically
python3 enginex.py -d example.com
```

> No `pip install -r requirements.txt` needed. EngineX bootstraps its own dependencies.

**Optional: Add Go to PATH** (if not already set):
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

# Stealth / slow rate (avoid detection/blocking)
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
# Most common real-world run (after first setup)
python3 enginex.py -d example.com --skip-install --skip-wordlists -r 50

# Light recon only (no fuzzing, no sqli)
python3 enginex.py -d example.com --no-fuzz --no-sqli --skip-install

# Full scan, slow and stealthy, skip install
python3 enginex.py -d example.com --skip-install -r 15

# Full scan from scratch (first time on new machine)
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
tail -f enginex_bg.log

# Check what phase the scan is currently on
cat status.txt

# View full log
cat enginex.log
```

---

### Pause / Resume Mid-Scan

```bash
# Pause a running scan
touch pause.flag

# Resume it
rm pause.flag
```

> The scan polls every 5 seconds and resumes from where it left off. No data is lost.

---

### Output & Reports

```bash
# View all generated output files
ls -lh output/

# Subdomain results
cat output/example.com_subs.txt

# Live hosts (with title and tech stack)
cat output/example.com_live.txt

# Crawled URLs
cat output/example.com_urls.txt

# Parameter URLs (for vuln scanning)
cat output/example.com_params.txt

# Nuclei findings
cat output/example.com_nuclei.txt

# XSS reflection hits
cat output/example.com_xss_basic.txt

# Dalfox XSS results
cat output/example.com_dalfox.txt

# SSRF candidates
cat output/example.com_ssrf.txt

# IDOR candidates
cat output/example.com_idor.txt

# LFI hits
cat output/example.com_lfi.txt

# Open redirect hits
cat output/example.com_redirect.txt

# Classified vuln categories (from nuclei)
cat output/classified_xss.txt
cat output/classified_sqli.txt
cat output/classified_rce.txt
cat output/classified_lfi.txt
cat output/classified_ssrf.txt
cat output/classified_idor.txt

# Pretty-print JSON report
python3 -m json.tool output/example.com_*_report.json

# Read Markdown report
cat output/example.com_*_report.md
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
| `--no-sqli` | Skip sqlmap SQLi scan | Off |
| `--bg` | Run in background via nohup | Off |

---

## 🎯 Recommended Bug Bounty Workflow

```bash
# ── Day 1 — First run on new machine ──────────────────────────
# Full setup: installs tools, downloads wordlists, runs all scans
python3 enginex.py -d target.com -r 30

# ── Day 2+ — Tools already installed ──────────────────────────
# Skip install + wordlists, standard rate
python3 enginex.py -d target.com --skip-install --skip-wordlists -r 50

# ── Re-run after crash or partial scan ────────────────────────
# Skip heavy setup, skip sqli to speed up
python3 enginex.py -d target.com --skip-install --skip-wordlists --no-sqli -r 40

# ── Overnight scan — leave it running ─────────────────────────
python3 enginex.py -d target.com -r 20 --skip-install --skip-wordlists --bg
tail -f enginex_bg.log
```

---

## 📁 Output Structure

```
output/
├── target.com_subs.txt          # All discovered subdomains
├── target.com_live.txt          # Live hosts with tech/title info
├── target.com_urls.txt          # All crawled URLs
├── target.com_params.txt        # URLs with parameters (for vuln scanning)
├── target.com_nuclei.txt        # Raw nuclei findings
├── target.com_dalfox.txt        # Dalfox XSS results
├── target.com_xss_basic.txt     # XSS reflection hits
├── target.com_ssrf.txt          # SSRF candidates
├── target.com_idor.txt          # IDOR candidates
├── target.com_lfi.txt           # LFI hits
├── target.com_redirect.txt      # Open redirect hits
├── classified_xss.txt           # Nuclei → XSS classified
├── classified_sqli.txt          # Nuclei → SQLi classified
├── classified_rce.txt           # Nuclei → RCE classified
├── classified_lfi.txt           # Nuclei → LFI classified
├── classified_ssrf.txt          # Nuclei → SSRF classified
├── classified_idor.txt          # Nuclei → IDOR classified
├── ffuf/                        # Per-host FFUF fuzzing results (JSON)
├── sqlmap/                      # sqlmap output directory
├── target.com_YYYYMMDD_report.json   # Full machine-readable report
└── target.com_YYYYMMDD_report.md     # Human-readable Markdown report

wordlists/
├── PayloadsAllTheThings/        # Exploit payloads wordlist
└── SecLists-common/             # Discovery wordlists (FFUF)

enginex.log        # Full execution log with timestamps
enginex_bg.log     # Background mode log
status.txt         # Current scan phase (live status)
pause.flag         # Create this file to pause, delete to resume
```

---

## 🛡️ Vulnerability Coverage

| Vulnerability | Method | Tool Used |
|--------------|--------|-----------|
| XSS (Reflected) | Active parameter injection | dalfox + custom scanner |
| SQL Injection | Active exploitation | sqlmap |
| SSRF | Parameter keyword matching | Custom detector |
| IDOR | Parameter pattern analysis | Custom detector |
| LFI / Path Traversal | Payload injection + response analysis | Custom detector |
| Open Redirect | Active redirect injection + URL verification | Custom detector |
| OWASP Top 10 (broad) | Template-based scanning | nuclei |
| RCE, SSTI, XXE, etc. | Template-based scanning | nuclei |
| Hidden Directories | Brute-force fuzzing | ffuf + SecLists |
| Exposed Services | Port + service enumeration | nmap |

---

## ⚠️ Disclaimer

> **EngineX is intended strictly for authorized security testing and educational purposes.**
>
> - Only run EngineX against domains you **own** or have **explicit written permission** to test.
> - Unauthorized scanning of systems is **illegal** under the Computer Fraud and Abuse Act (CFAA), IT Act 2000, and equivalent laws in most jurisdictions.
> - The developer assumes **no liability** for misuse or damage caused by this tool.
> - Always operate within the scope defined in your bug bounty program's policy.

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
| [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | swisskyrepo | Payload wordlists |
| [SecLists](https://github.com/danielmiessler/SecLists) | danielmiessler | Security wordlists |

---

<div align="center">

**Built with ⚡ by RAVX**

*If EngineX helped you find a bug, consider giving the repo a ⭐*

[![GitHub stars](https://img.shields.io/github/stars/RAVX/enginex?style=social)](https://github.com/RAVX/enginex)

</div>
