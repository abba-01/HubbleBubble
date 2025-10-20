---
name: Reproducibility Failure
about: Report when you cannot reproduce the documented results
title: "[REPRO] "
labels: reproducibility, bug, needs-investigation
assignees: ''
---

## 🔴 Reproducibility Failure Report

Thank you for reporting this! Reproducibility issues are our highest priority.

---

## Environment Information

**Operating System**:
- [ ] Linux (distribution: ___________, version: _______)
- [ ] macOS (version: _______)
- [ ] Windows (WSL2 / Docker / Other: _______)

**Python Version**:
```bash
python --version
# Output:
```

**Installation Method**:
- [ ] pip install -r requirements.txt
- [ ] Docker/Podman
- [ ] Manual installation
- [ ] Other: __________

---

## What I Did

### Setup Steps
```bash
# Paste the EXACT commands you ran
# For example:
git clone https://github.com/abba-01/HubbleBubble.git
cd HubbleBubble
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Validation Commands
```bash
# Commands that failed or produced unexpected results
```

---

## Expected Result

What the README or documentation said would happen:

```
# Example: "✓ 100% package match with canonical environment"
```

---

## Actual Result

What actually happened:

```
# Paste error messages, unexpected output, or different results
```

---

## Environment Verification

Please run and paste the output:

```bash
python rent/phase1_provenance/verify_environment.py --mode audit
```

<details>
<summary>Environment Verification Output</summary>

```
# Paste full output here
```

</details>

---

## Hash Mismatches (if applicable)

If Phase IV showed hash differences:

**Which files didn't match?**
- [ ] loao.json
- [ ] grids.json
- [ ] bootstrap.json
- [ ] inject.json
- [ ] Other: __________

**Hash audit output**:
```bash
# Paste relevant section from:
python rent/run_rent.py --mode audit --quick
```

---

## Logs

<details>
<summary>Full Validation Log</summary>

```
# Paste any error logs from outputs/logs/
# Or full terminal output
```

</details>

---

## Additional Context

### Things I've Tried
- [ ] Created fresh virtual environment
- [ ] Re-installed dependencies
- [ ] Checked Python version
- [ ] Verified internet connection
- [ ] Read Troubleshooting section in README

### System Details
- RAM: _____ GB
- Disk space available: _____ GB
- CPU cores: _____
- Running inside VM/container: Yes / No

### Other Information
<!-- Any other context, screenshots, or details that might help -->

---

## Reproducibility Checklist

To help us diagnose, please confirm:

- [ ] I used a fresh virtual environment (not global Python)
- [ ] I installed exact versions from requirements.txt
- [ ] I'm in the HubbleBubble root directory
- [ ] I have internet access (for pip installs)
- [ ] I read the Troubleshooting section

---

**Note**: Expected variations (OK to have):
- ✅ IERS data version drift (astropy-iers-data)
- ✅ Missing optional files (baseline_measurements.json, etc.)
- ✅ Stochastic file differences (bootstrap.json, inject.json - if not using seed)

Unexpected issues (please report):
- ❌ Core package mismatches (numpy, scipy, pandas)
- ❌ Deterministic file hash differences (loao.json, grids.json)
- ❌ Validation scripts crashing
- ❌ Missing required data files

---

Thank you for helping improve reproducibility! 🔬
