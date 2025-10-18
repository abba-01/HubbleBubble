# H₀ Concordance Validation Report

**Generated**: {{ date }}
**Environment**: {{ env }}
**HubbleBubble Version**: 1.0.0

---

## Executive Summary

**Result**: H₀ = {{ "%.2f"|format(h0.mu_star) }} ± {{ "%.2f"|format(h0.sigma_star) }} km s⁻¹ Mpc⁻¹

**Validation Status**: {% if all_passed %}✅ ALL GATES PASSED{% else %}⚠️ ONE OR MORE GATES FAILED{% endif %}

**Tension to Planck**: {{ "%.2f"|format(h0.z_planck) }}σ ({% if h0.z_planck < 1.0 %}CONCORDANCE{% elif h0.z_planck < 2.0 %}NEAR-CONCORDANCE{% else %}TENSION{% endif %})

---

## 1. Inputs

### Baseline Measurements

| Measurement | H₀ (km s⁻¹ Mpc⁻¹) | σ (km s⁻¹ Mpc⁻¹) | Source |
|-------------|-------------------|-------------------|--------|
| **Planck** (CMB) | {{ "%.2f"|format(h0.inputs.mu_planck) }} | {{ "%.2f"|format(h0.inputs.sigma_planck) }} | Planck 2018 |
| **SH0ES** (original) | 73.59 | 1.56 | Riess et al. 2022 |
| **SH0ES** (corrected) | {{ "%.2f"|format(h0.inputs.mu_shoes) }} | {{ "%.2f"|format(h0.inputs.sigma_shoes) }} | After anchor + P-L corrections |

### Systematic Corrections Applied

| Correction | Value (km s⁻¹ Mpc⁻¹) | Description |
|------------|----------------------|-------------|
| Anchor bias | -1.92 | MW anchor systematically high vs LMC/NGC4258 |
| P-L relation | -0.22 | Period-luminosity modeling variations |
| **Total** | **-2.14** | SH0ES: 73.59 → 71.45 km s⁻¹ Mpc⁻¹ |

### Epistemic Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Δ_T | {{ "%.2f"|format(h0.inputs.delta_T) }} | Epistemic distance (observer tensor) |
| f_systematic | {{ "%.2f"|format(h0.inputs.f_systematic) }} | Fraction attributed to systematic |

---

## 2. Concordance Result

### Headline Result

**H₀ = {{ "%.2f"|format(h0.mu_star) }} ± {{ "%.2f"|format(h0.sigma_star) }} km s⁻¹ Mpc⁻¹**

This represents a weighted merge of Planck CMB and SH0ES distance ladder measurements after:
1. Systematic corrections to SH0ES (anchor + P-L biases)
2. Epistemic penalty for methodological differences

### Epistemic Penalty

**u_epistemic = {{ "%.2f"|format(h0.u_epistemic) }} km s⁻¹ Mpc⁻¹**

Computed from: u = (disagreement/2) × Δ_T × (1 - f_systematic)

### Effective Uncertainties

| Measurement | Raw σ | Effective σ | Inflation |
|-------------|-------|-------------|-----------|
| Planck | {{ "%.2f"|format(h0.inputs.sigma_planck) }} | {{ "%.2f"|format(h0.sigma_eff_planck) }} | {{ "%.0f"|format((h0.sigma_eff_planck/h0.inputs.sigma_planck - 1)*100) }}% |
| SH0ES (corr) | {{ "%.2f"|format(h0.inputs.sigma_shoes) }} | {{ "%.2f"|format(h0.sigma_eff_shoes) }} | {{ "%.0f"|format((h0.sigma_eff_shoes/h0.inputs.sigma_shoes - 1)*100) }}% |

Epistemic penalty added in quadrature to account for methodological differences.

### Merge Weights

| Measurement | Weight | Fraction |
|-------------|--------|----------|
| Planck | {{ "%.4f"|format(h0.w_planck) }} | {{ "%.1f"|format(h0.w_planck_frac*100) }}% |
| SH0ES (corr) | {{ "%.4f"|format(h0.w_shoes) }} | {{ "%.1f"|format(h0.w_shoes_frac*100) }}% |

Higher weight to Planck due to tighter uncertainty.

### Tensions

| Comparison | Gap (km s⁻¹ Mpc⁻¹) | Tension (σ) | Status |
|------------|---------------------|-------------|--------|
| Concordance vs Planck | {{ "%.2f"|format(h0.mu_star - h0.inputs.mu_planck) }} | {{ "%.2f"|format(h0.z_planck) }} | {% if h0.z_planck < 1.0 %}✅ CONCORDANCE{% elif h0.z_planck < 2.0 %}⚠️ NEAR-CONCORDANCE{% else %}❌ TENSION{% endif %} |
| Concordance vs SH0ES (orig) | {{ "%.2f"|format(h0.mu_star - 73.59) }} | {{ "%.2f"|format(h0.z_shoes_orig) }} | TENSION |
| Concordance vs SH0ES (corr) | {{ "%.2f"|format(h0.disagreement - (73.59 - h0.inputs.mu_shoes)) }} | {{ "%.2f"|format(h0.z_shoes_corr) }} | {% if h0.z_shoes_corr < 2.0 %}MILD{% else %}SIGNIFICANT{% endif %} |

---

## 3. Validation Suite Results

### 3.1 Leave-One-Anchor-Out (LOAO)

**Purpose**: Test robustness to anchor choice
**Method**: Re-run concordance with each anchor (MW, LMC, NGC4258) removed
**Gate**: z_planck ≤ {{ loao.gate }}σ for ALL variants

**Result**: {% if loao.passed %}✅ PASS{% else %}❌ FAIL{% endif %} (max z_planck = {{ "%.2f"|format(loao.max_z_planck) }}σ)

| Scenario | Excluded Anchor | Concordance H₀ | z_planck | Status |
|----------|-----------------|----------------|----------|--------|
{% for name, result in loao.scenarios.items() -%}
| {{ name }} | {{ result.excluded_anchor if result.excluded_anchor != "none" else "—" }} | {{ "%.2f"|format(result.mu_star) }} ± {{ "%.2f"|format(result.sigma_star) }} | {{ "%.2f"|format(result.z_planck) }} | {% if result.z_planck <= loao.gate %}✓{% else %}✗{% endif %} |
{% endfor %}

**Interpretation**: {% if loao.passed %}Result is robust to anchor removal. Concordance maintained regardless of which anchor is excluded.{% else %}Result depends on specific anchor choice. Further investigation needed.{% endif %}

---

### 3.2 Grid-Scan (ΔT × f_systematic)

**Purpose**: Test sensitivity to epistemic parameter choices
**Method**: 17×17 grid over (ΔT ∈ [1.0, 1.8], f_sys ∈ [0.3, 0.7])
**Gate**: Median z_planck ∈ [{{ grid.gate.min }}, {{ grid.gate.max }}]σ

**Result**: {% if grid.passed %}✅ PASS{% else %}❌ FAIL{% endif %} (median z_planck = {{ "%.2f"|format(grid.statistics.z_planck_median) }}σ)

| Statistic | z_planck (σ) |
|-----------|--------------|
| Median | {{ "%.2f"|format(grid.statistics.z_planck_median) }} |
| Mean | {{ "%.2f"|format(grid.statistics.z_planck_mean) }} ± {{ "%.2f"|format(grid.statistics.z_planck_std) }} |
| Range | [{{ "%.2f"|format(grid.statistics.z_planck_min) }}, {{ "%.2f"|format(grid.statistics.z_planck_max) }}] |
| IQR | [{{ "%.2f"|format(grid.statistics.z_planck_p25) }}, {{ "%.2f"|format(grid.statistics.z_planck_p75) }}] |

**Interpretation**: {% if grid.passed %}Concordance is stable across reasonable epistemic parameter variations. Result is not fine-tuned.{% else %}Result is sensitive to epistemic parameter choices. Requires further justification.{% endif %}

---

### 3.3 Bootstrap ({{ boot.n_iterations }} iterations)

**Purpose**: Quantify uncertainty in correction estimation
**Method**: Resample 210-config grid, re-estimate corrections, re-run merge
**Gate**: z_planck 95th percentile ≤ {{ boot.gate }}σ

**Result**: {% if boot.passed %}✅ PASS{% else %}❌ FAIL{% endif %} (p95 z_planck = {{ "%.2f"|format(boot.statistics.z_planck.p95) }}σ)

| Quantity | Median | Mean ± Std |
|----------|--------|------------|
| H₀ (km s⁻¹ Mpc⁻¹) | {{ "%.2f"|format(boot.statistics.h0.median) }} | {{ "%.2f"|format(boot.statistics.h0.mean) }} ± {{ "%.2f"|format(boot.statistics.h0.std) }} |
| z_planck (σ) | {{ "%.2f"|format(boot.statistics.z_planck.median) }} | {{ "%.2f"|format(boot.statistics.z_planck.mean) }} ± {{ "%.2f"|format(boot.statistics.z_planck.std) }} |
| Anchor correction | — | {{ "%.2f"|format(boot.statistics.corrections.anchor_mean) }} ± {{ "%.2f"|format(boot.statistics.corrections.anchor_std) }} |
| P-L correction | — | {{ "%.3f"|format(boot.statistics.corrections.pl_mean) }} ± {{ "%.3f"|format(boot.statistics.corrections.pl_std) }} |

**Interpretation**: {% if boot.passed %}Correction estimation uncertainty does not compromise concordance. Robust to resampling.{% else %}Large uncertainty in corrections leads to tension. More data or refined methods needed.{% endif %}

---

### 3.4 Synthetic Injection/Recovery ({{ inject.n_trials }} trials)

**Purpose**: Test calibration and bias
**Method**: Plant truth H₀ ∈ [67.3, 67.5], simulate SH0ES with biases, recover via concordance
**Gates**:
- |bias| median ≤ {{ inject.gates.bias_max }} km s⁻¹ Mpc⁻¹
- z_planck median ≤ {{ inject.gates.z_planck_max }}σ

**Result**: {% if inject.passed %}✅ PASS{% else %}❌ FAIL{% endif %}

| Gate | Value | Threshold | Status |
|------|-------|-----------|--------|
| |bias| median | {{ "%.3f"|format(inject.statistics.bias.median) }} km s⁻¹ Mpc⁻¹ | ≤ {{ inject.gates.bias_max }} | {% if inject.gates.bias_passed %}✓{% else %}✗{% endif %} |
| z_planck median | {{ "%.2f"|format(inject.statistics.z_planck.median) }}σ | ≤ {{ inject.gates.z_planck_max }} | {% if inject.gates.z_planck_passed %}✓{% else %}✗{% endif %} |

**Planted biases**:
- Anchor: {{ "%.2f"|format(inject.planted_biases.anchor) }} km s⁻¹ Mpc⁻¹
- P-L: {{ "%.2f"|format(inject.planted_biases.pl) }} km s⁻¹ Mpc⁻¹

**Interpretation**: {% if inject.passed %}Methodology correctly recovers planted truth with minimal bias. Calibration validated.{% else %}Systematic bias detected in recovery. Methodology requires refinement.{% endif %}

---

## 4. Overall Validation Summary

| Validation Suite | Gate | Result | Status |
|------------------|------|--------|--------|
| **LOAO** | Max z_planck ≤ {{ loao.gate }}σ | {{ "%.2f"|format(loao.max_z_planck) }}σ | {% if loao.passed %}✅ PASS{% else %}❌ FAIL{% endif %} |
| **Grid-scan** | Median z_planck ∈ [{{ grid.gate.min }}, {{ grid.gate.max }}]σ | {{ "%.2f"|format(grid.statistics.z_planck_median) }}σ | {% if grid.passed %}✅ PASS{% else %}❌ FAIL{% endif %} |
| **Bootstrap** | p95 z_planck ≤ {{ boot.gate }}σ | {{ "%.2f"|format(boot.statistics.z_planck.p95) }}σ | {% if boot.passed %}✅ PASS{% else %}❌ FAIL{% endif %} |
| **Injection** | |bias| ≤ {{ inject.gates.bias_max }}, z ≤ {{ inject.gates.z_planck_max }}σ | {{ "%.3f"|format(inject.statistics.bias.median) }}, {{ "%.2f"|format(inject.statistics.z_planck.median) }}σ | {% if inject.passed %}✅ PASS{% else %}❌ FAIL{% endif %} |

### Final Verdict

{% if all_passed %}
**✅ ALL VALIDATION GATES PASSED**

The concordance result H₀ = {{ "%.2f"|format(h0.mu_star) }} ± {{ "%.2f"|format(h0.sigma_star) }} km s⁻¹ Mpc⁻¹ has been validated by four independent methods:
- Robust to anchor choice (LOAO)
- Stable across parameter variations (Grid-scan)
- Uncertainty well-characterized (Bootstrap)
- Calibration verified (Injection)

**This result is publication-ready.**
{% else %}
**⚠️ ONE OR MORE VALIDATION GATES FAILED**

The concordance result requires further investigation before publication:
{% if not loao.passed %}- LOAO: Result depends on specific anchor choice{% endif %}
{% if not grid.passed %}- Grid-scan: Sensitive to epistemic parameter choices{% endif %}
{% if not boot.passed %}- Bootstrap: Large correction uncertainty{% endif %}
{% if not inject.passed %}- Injection: Systematic bias detected{% endif %}

**Recommendation**: Iterate analysis to address failed gates.
{% endif %}

---

## 5. Reproducibility

**Seed**: 172901 (fixed for all stochastic operations)
**Dependencies**: See `requirements.txt` (all versions pinned)
**Data checksums**: See `outputs/reproducibility/SHASUMS256.json`
**Provenance**: See `outputs/reproducibility/manifest.json`

### Container

```bash
podman build -t h0_rigorous:1.0 -f Containerfile .
podman run --rm -it -v $PWD:/work:Z -w /work h0_rigorous:1.0 make all
```

### Bare-metal

```bash
make all
```

---

**Generated by**: HubbleBubble v1.0.0
**Runtime**: {{ runtime if runtime else "N/A" }}
**Report**: `outputs/h0_validation_report.html`
