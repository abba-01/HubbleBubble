# HubbleBubble: Rigorous H₀ Concordance Validation Capsule

**Fully rigorous, non-optional, reproducible validation of the Hubble concordance result on RHEL 10**

**Result**: H₀ = 68.52 ± 1.29 km s⁻¹ Mpc⁻¹ (0.88σ to Planck, 76.8% tension reduction)

---

## Quick Start

```bash
# Clone and setup
cd /got/HubbleBubble
make all

# Or containerized (recommended for review)
podman build -t h0_rigorous:1.0 -f Containerfile .
podman run --rm -it -v $PWD:/work:Z -w /work h0_rigorous:1.0 make all
```

**Output**: `outputs/h0_validation_report.html` + pass/fail gates

---

## Overview

This capsule implements a **fully rigorous, non-optional, and reproducible** validation framework for the Hubble concordance analysis. It creates a locked research capsule that you (and any reviewer) can run end-to-end to produce:

1. **Data acquisition** with checksums and provenance
2. **Core concordance calculation** (systematic corrections + epistemic penalty)
3. **Four validation suites** (LOAO, grid-scan, bootstrap, synthetic injection)
4. **One-command HTML/PDF report**

### Design Principles

- ✅ **No optional steps**: Every component is required and enforced
- ✅ **Bit-reproducible**: Fixed seeds, pinned versions, checksummed data
- ✅ **Falsification-oriented**: Four independent validation methods with hard acceptance gates
- ✅ **Auditable**: USO/UHA/cDOI provenance for every result
- ✅ **Container-ready**: Podman/Docker for review isolation

---

## System Prerequisites (RHEL 10)

```bash
# Base development tools
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y git curl wget make gcc gcc-c++ openssl openssl-devel \
                    zlib zlib-devel bzip2 bzip2-devel xz xz-devel \
                    python3 python3-pip python3-virtualenv \
                    openblas openblas-devel lapack lapack-devel

# Container runtime (Podman is default on RHEL)
sudo dnf install -y podman

# Optional: TeX for PDF reports
sudo dnf install -y texlive texlive-collection-latexrecommended
```

**Why OpenBLAS/LAPACK?** Bootstrap and grid-scan get 3-10× faster with BLAS acceleration.

---

## Two Execution Modes

### A) Bare-metal (virtualenv)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel
python -m pip install -r requirements.txt
make all
```

### B) Containerized (recommended for review)
```bash
# Build (rootless)
podman build -t h0_rigorous:1.0 -f Containerfile .

# Run
podman run --rm -it \
  -v $PWD:/work:Z \
  -w /work \
  --name h0_capsule h0_rigorous:1.0 \
  make all
```

**Note**: Podman is rootless by default on RHEL, which reviewers prefer. If you must use Docker, rename `Containerfile` → `Dockerfile`.

---

## Project Layout

```text
HubbleBubble/
  README.md                   # This file
  Containerfile               # Podman/Docker container definition
  Makefile                    # One-command automation
  requirements.txt            # Pinned Python dependencies
  pyproject.toml              # Optional: tool configuration

  src/
    __init__.py
    config.py                 # All parameters, gates, seeds
    data_io.py                # Data acquisition with checksums
    planck.py                 # Planck CMB data processing
    shoes.py                  # SH0ES systematic corrections
    gaia.py                   # Gaia parallax data
    nu_algebra.py             # N/U algebra framework
    penalty.py                # Epistemic penalty calculation
    merge.py                  # Concordance merge with penalty

    validation/
      loao.py                 # Leave-One-Anchor-Out
      grids.py                # ΔT × f_systematic grid-scan
      bootstrap.py            # Bootstrap corrections + merge
      inject.py               # Synthetic injection/recovery

    report/
      build_report.py         # Compiles HTML/PDF
      templates/
        report.tpl.md         # Jinja2 template

  assets/                     # Cached downloads (checksummed)
    README.md
    planck/
    vizier/
    gaia/
    external/

  outputs/
    logs/
    figures/
    tables/
    results/
      loao.json
      grids.json
      bootstrap.json
      inject.json
    reproducibility/
      manifest.json
      SHASUMS256.txt
      USO/                    # Universal Science Objects
      UHA/                    # Universal Horizon Addresses

  LICENSE
```

---

## Core Configuration

All parameters, gates, and seeds are defined in `src/config.py`:

### Parameters

```python
@dataclass(frozen=True)
class Epistemic:
    delta_T = 1.36          # Epistemic distance (observer tensor)
    f_systematic = 0.50     # Fraction attributed to systematic

    # Grid-scan bounds:
    delta_T_min = 1.0
    delta_T_max = 1.8
    f_sys_min  = 0.3
    f_sys_max  = 0.7

@dataclass(frozen=True)
class Baseline:
    planck_mu = 67.27
    planck_sigma_raw = 0.60

    shoes_mu_orig = 73.59
    shoes_sigma_orig = 1.56

    # Corrections (from Paper 3 analysis):
    corr_anchor = -1.92     # MW anchor bias
    corr_pl     = -0.22     # P-L relation bias
    shoes_sigma_corr = 1.89 # Propagated from 210-config spread
```

### Acceptance Gates (REQUIRED)

```python
@dataclass(frozen=True)
class Gates:
    loao_sigma_planck_max = 1.5
    grid_sigma_planck_median_min = 0.9
    grid_sigma_planck_median_max = 1.1
    inject_abs_bias_max = 0.3           # km/s/Mpc
    inject_sigma_planck_max = 1.0
    bootstrap_sigma_planck_p95_max = 1.2
```

**If any gate fails, the pipeline returns non-zero and prints a red banner.**

### Seeds (REQUIRED for reproducibility)

```python
@dataclass(frozen=True)
class Seeds:
    master = 172901  # Fixed seed for all stochastic operations
```

---

## Validation Suites

### 1. Leave-One-Anchor-Out (LOAO)

**Purpose**: Test robustness to anchor choice

**Method**: Re-run concordance with each anchor (MW, LMC, NGC4258) removed

**Acceptance Gate**: z_planck ≤ 1.5σ for all variants

**Run**:
```bash
python src/validation/loao.py --out outputs/results/loao.json
```

---

### 2. Grid-Scan (ΔT × f_systematic)

**Purpose**: Test sensitivity to epistemic parameters

**Method**: 17×17 grid over (ΔT ∈ [1.0, 1.8], f_sys ∈ [0.3, 0.7])

**Acceptance Gate**: Median z_planck ∈ [0.9, 1.1]σ

**Run**:
```bash
python src/validation/grids.py --out outputs/results/grids.json
```

---

### 3. Bootstrap (10,000 iterations)

**Purpose**: Quantify uncertainty in correction estimation

**Method**: Resample 210-config grid, re-estimate anchor + P-L corrections, re-run merge

**Acceptance Gate**: z_planck 95th percentile ≤ 1.2σ

**Run**:
```bash
python src/validation/bootstrap.py --iters 10000 --out outputs/results/bootstrap.json
```

---

### 4. Synthetic Injection/Recovery

**Purpose**: Test bias and calibration

**Method**: Plant truth H₀ ∈ [67.3, 67.5], simulate SH0ES with planted biases, recover via concordance

**Acceptance Gate**:
- Median |bias| ≤ 0.3 km s⁻¹ Mpc⁻¹
- Median z_planck ≤ 1.0σ

**Run**:
```bash
python src/validation/inject.py --trials 2000 --out outputs/results/inject.json
```

---

## Makefile Targets

```bash
make all         # Complete pipeline: setup → data → validate → report
make setup       # Create virtualenv, install dependencies
make data        # Fetch and checksum all data
make validate    # Run all 4 validation suites
make report      # Generate HTML/PDF report
make clean       # Remove outputs
```

---

## Expected Results

### Headline Concordance

**H₀ = 68.52 ± 1.29 km s⁻¹ Mpc⁻¹**

**Breakdown**:
- Planck: 67.27 ± 0.60 → 1.54 km/s/Mpc (effective, with epistemic penalty)
- SH0ES: 73.59 ± 1.56 → 71.45 ± 1.89 (corrected for anchor + P-L bias)
- Epistemic penalty: u_epistemic = 1.42 km/s/Mpc

**Tensions**:
- To Planck: **0.88σ** (CONCORDANCE ACHIEVED)
- To SH0ES (corrected): 1.28σ
- Baseline (Planck vs SH0ES original): 3.78σ
- **Tension reduction: 76.8%**

### Validation Pass Criteria

All four suites must pass for the result to be accepted:

| Suite | Gate | Expected |
|-------|------|----------|
| LOAO | All variants z_planck ≤ 1.5σ | PASS |
| Grid-scan | Median z_planck ∈ [0.9, 1.1]σ | PASS |
| Bootstrap | z_planck p95 ≤ 1.2σ | PASS |
| Injection | Median \|bias\| ≤ 0.3 km/s/Mpc, z ≤ 1.0σ | PASS |

---

## Reproducibility Hardening

### 1. Fixed Seeds
All stochastic operations use `Seeds.master = 172901` from `config.py`

### 2. Checksums
All downloaded data verified with SHA-256:
```
outputs/reproducibility/SHASUMS256.txt
```

### 3. Provenance
Every result JSON includes:
- Input parameters
- Software version (git hash)
- Container digest (if containerized)
- Timestamp (ISO 8601 UTC)
- Execution environment

### 4. USO/UHA/cDOI Framework

**Universal Science Object (USO)**: Contains corrected values, penalty, weights, provenance
- Stored in: `outputs/reproducibility/USO/*.json`
- Schema-validated with `jsonschema`

**Universal Horizon Address (UHA)**: Encodes observer tensor components (a, ξ, û, {c, f₂₁})
- Stored in: `outputs/reproducibility/UHA/*.json`

**Cosmic DOI (cDOI)**: Provisional identifier for self-decoding metadata
- Format: `cDOI://h0-concordance/v1.0/<hash>`

---

## Dependencies

All versions pinned for bit-reproducibility:

```txt
numpy==2.1.2
scipy==1.13.1
pandas==2.2.2
matplotlib==3.9.2
seaborn==0.13.2
astropy==6.1.0
astroquery==0.4.7
pyyaml==6.0.2
jinja2==3.1.4
markdown==3.7
jsonschema==4.23.0
tabulate==0.9.0
tqdm==4.66.5
```

For stricter locking, use `pip-tools` to generate a compiled lockfile.

---

## Container Details

**Base Image**: `quay.io/pypa/manylinux_2_28_x86_64` (RHEL 10 compatible)

**Includes**:
- OpenBLAS + LAPACK for numerical acceleration
- TeX Live for PDF generation
- Python 3.11 virtualenv
- All pinned dependencies

**Build**:
```bash
podman build -t h0_rigorous:1.0 -f Containerfile .
```

**Run**:
```bash
podman run --rm -it -v $PWD:/work:Z -w /work h0_rigorous:1.0 bash
```

---

## Data Sources

### Planck 2018
- **Source**: ESA Planck Legacy Archive
- **Data**: MCMC chains (base_plikHM_TTTEEE_lowl_lowE)
- **Parameters**: H₀, ω_c, ω_b, n_s, τ, A_s
- **Checksum**: SHA-256 verified

### SH0ES 2016-2022
- **Source**: VizieR J/ApJ/826/56 (Riess et al. 2016)
- **Data**: 210 systematic configurations
- **Anchors**: NGC4258 (N=24), Milky Way (M=23), LMC (L=23)
- **Checksum**: SHA-256 verified

### Gaia EDR3 (optional)
- **Source**: Gaia Archive
- **Data**: Parallax zero-point systematics
- **Usage**: MW anchor caution validation
- **Checksum**: SHA-256 verified

---

## Using Claude Code CLI

Point Claude Code at this repository for:

1. **Alternative estimators**: Add robust anchor correction (Huber, trimmed mean)
2. **Enhanced plotting**: PPC plots, grid heatmaps, bootstrap histograms
3. **Methods supplement**: Auto-generate from validation JSONs

**Example**:
```
"Add a robust anchor-correction estimator to src/shoes.py (Huber, τ=1.5),
rewire bootstrap to try mean/trimmed/Huber and record ΔH₀ distributions by method."
```

---

## Scientific Context

### The Hubble Tension

**Early-universe (Planck CMB)**: H₀ ≈ 67.27 ± 0.60 km s⁻¹ Mpc⁻¹
**Late-universe (SH0ES)**: H₀ ≈ 73.59 ± 1.56 km s⁻¹ Mpc⁻¹
**Baseline discrepancy**: 6.32 km s⁻¹ Mpc⁻¹ (3.78σ)

### Our Approach

**Hypothesis**: Tension is primarily systematic (anchor-dependent), not new physics

**Method**:
1. **Systematic decomposition**: Identify dominant biases (anchor: 1.92, P-L: 0.22 km/s/Mpc)
2. **Correction**: Apply to SH0ES (73.59 → 71.45 km/s/Mpc)
3. **Epistemic penalty**: Account for methodological differences (u_epistemic = 1.42 km/s/Mpc)
4. **Weighted merge**: Inverse-variance + epistemic penalty

**Result**: H₀ = 68.52 ± 1.29 km s⁻¹ Mpc⁻¹ (0.88σ to Planck)

### Interpretation

✅ **Concordance achieved**: <1σ residual to Planck
✅ **Tension reduction**: 76.8% (3.78σ → 0.88σ)
✅ **Systematic identification**: MW anchor bias is THE dominant effect
✅ **No new physics required**: ΛCDM remains viable

⚠️ **Caveat**: Assumes MW anchor bias is ~50% of observed spread (conservative)
⚠️ **Future test**: JWST independent Cepheid calibration will validate/refute

---

## Publication-Ready Outputs

### 1. Validation Report
**File**: `outputs/h0_validation_report.html`
**Contents**:
- Headline concordance result
- All four validation suite results
- Pass/fail gates
- Figures (grid heatmaps, bootstrap distributions, injection recovery)
- Provenance metadata

### 2. Data Tables
**Location**: `outputs/tables/`
**Formats**: CSV, LaTeX, Markdown
**Contents**: All numerical results with uncertainties

### 3. Figures
**Location**: `outputs/figures/`
**Formats**: PNG (300 DPI), PDF (vector)
**Contents**:
- Tension evolution (before/after corrections)
- Grid-scan heatmap (ΔT × f_systematic)
- Bootstrap distributions (z_planck histogram)
- Injection recovery (truth vs recovered)
- LOAO comparison (all anchor variants)

### 4. Reproducibility Package
**Location**: `outputs/reproducibility/`
**Contents**:
- `manifest.json` (complete provenance)
- `SHASUMS256.txt` (all data checksums)
- `USO/*.json` (Universal Science Objects)
- `UHA/*.json` (Universal Horizon Addresses)
- `environment.txt` (conda/pip freeze)

---

## Troubleshooting

### Issue: Missing BLAS/LAPACK
**Symptom**: Slow bootstrap/grid-scan
**Fix**:
```bash
sudo dnf install -y openblas openblas-devel lapack lapack-devel
pip install --force-reinstall --no-binary :all: numpy scipy
```

### Issue: Container permission denied
**Symptom**: `Error: writing blob: adding layer with blob`
**Fix**: Use rootless Podman (default) or add `:Z` to volume mount
```bash
podman run --rm -it -v $PWD:/work:Z -w /work h0_rigorous:1.0 bash
```

### Issue: Data download fails
**Symptom**: `astroquery` timeout
**Fix**: Use pre-cached assets in `assets/` directory
```bash
# Copy pre-downloaded data
cp -r /backup/assets/* assets/
make validate  # Skip data step
```

### Issue: Validation gate failure
**Symptom**: `FAILED: z_planck > 1.5σ`
**Fix**: This is a **research finding**, not a bug. Investigate:
1. Check correction estimates (anchor spread, P-L variation)
2. Review epistemic parameters (ΔT, f_systematic)
3. Examine bootstrap distribution (systematic vs statistical)
4. Do NOT claim concordance; iterate analysis

---

## Citation

If you use this capsule in your research, please cite:

```bibtex
@software{hubblebubble2025,
  author = {Martin, Eric},
  title = {HubbleBubble: Rigorous H₀ Concordance Validation Capsule},
  year = {2025},
  url = {https://github.com/yourorg/HubbleBubble},
  version = {1.0}
}

@article{h0concordance2025,
  author = {Martin, Eric},
  title = {Resolving the Hubble Tension through Systematic Anchor Calibration and Epistemic Encoding},
  journal = {TBD},
  year = {2025},
  note = {In preparation}
}
```

---

## License

MIT License (see LICENSE file)

---

## References

- **Planck Collaboration** (2018). "Planck 2018 results. VI. Cosmological parameters." *A&A* 641, A6.
- **Riess et al.** (2022). "A Comprehensive Measurement of the Local Value of the Hubble Constant..." *ApJ* 934, L7.
- **Pietrzyński et al.** (2019). "A distance to the Large Magellanic Cloud..." *Nature* 567, 200–203.
- **Reid et al.** (2019). "An Improved Distance to NGC 4258..." *ApJ* 886, L27.
- **Groenewegen et al.** (2021). "Gaia EDR3 parallax zero-point..." *A&A* 654, A20.

---

## Acknowledgments

- **Planck Collaboration** for CMB data
- **SH0ES Team** for systematic grid data
- **Gaia Collaboration** for parallax data
- **Claude Code CLI** for automated validation assistance
- **RHEL 10** for enterprise-grade reproducibility

---

## Contact

**Author**: Eric Martin
**Institution**: TBD
**Email**: TBD
**Repository**: TBD

---

**Last Updated**: 2025-10-18
**Version**: 1.0.0
**Status**: Production-ready validation capsule

---

## Appendix: Quick Reference

### One-Line Commands

```bash
# Full pipeline (bare-metal)
make all

# Full pipeline (container)
podman run --rm -it -v $PWD:/work:Z -w /work h0_rigorous:1.0 make all

# Individual validations
python src/validation/loao.py --out outputs/results/loao.json
python src/validation/grids.py --out outputs/results/grids.json
python src/validation/bootstrap.py --iters 10000 --out outputs/results/bootstrap.json
python src/validation/inject.py --trials 2000 --out outputs/results/inject.json

# Generate report
python src/report/build_report.py --out outputs/h0_validation_report.html --pdf
```

### Expected Runtime

| Task | Bare-metal | Container | Notes |
|------|------------|-----------|-------|
| Data acquisition | 2-5 min | 2-5 min | Depends on network |
| LOAO | 10 sec | 15 sec | 4 scenarios |
| Grid-scan | 2 min | 3 min | 289 evaluations |
| Bootstrap | 15-30 min | 20-40 min | 10,000 iterations |
| Injection | 5-10 min | 8-15 min | 2,000 trials |
| Report | 5 sec | 10 sec | Jinja2 templating |
| **Total** | **25-50 min** | **35-65 min** | With BLAS |

### Disk Usage

```
assets/          ~500 MB  (Planck chains, VizieR tables, Gaia)
outputs/         ~50 MB   (results, figures, reproducibility)
container image  ~2 GB    (if using Podman/Docker)
```

---

**END OF README**
