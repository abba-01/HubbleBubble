# RENT Protocol: Rebuild Everything, Nothing Trusted

**Version**: 1.0
**Date**: 2025-10-18
**Philosophy**: "If you're not trying to break it, you're not really testing it."
**Core Principle**: "Spooky is fine. Unfalsifiable is not."

---

## Overview

The RENT (Rebuild Everything, Nothing Trusted) protocol is a **forensic validation suite** designed to adversarially test the HubbleBubble concordance claims. Unlike standard validation which confirms expected results, RENT actively attempts to:

- **Break the analysis** through edge cases
- **Find discrepancies** between claimed and recomputed values
- **Verify zero assumptions** - rebuild everything from first principles
- **Cross-validate** against independent implementations and external data

**Assumption**: Trust nothing. Verify everything.

---

## Seven-Phase Validation Protocol

### Phase I: Provenance Reconstruction

**Goal**: Verify the computational environment is exactly as claimed.

**Steps**:
1. Parse `requirements.txt` and `pip-freeze.txt`
2. Compute SHA-256 of every installed package wheel
3. Compare against documented checksums
4. Verify `Containerfile` produces bit-identical environment
5. Build data flow graph from `Makefile` targets
6. Document complete input → output lineage

**Pass Criteria**:
- All package hashes match
- No circular dependencies detected
- Complete provenance chain documented

**Failure Mode**:
- Any hash mismatch → **CRITICAL FAILURE**
- Missing provenance → **FAIL**

---

### Phase II: Re-execution from Scratch

**Goal**: Independently recompute all results starting from raw data.

**Steps**:
1. **Anchor correction**: Recompute from `assets/vizier/*.csv`
   - Load raw SH0ES systematic grid
   - Compute MW, LMC, NGC4258 means
   - Calculate anchor correction: -0.5 × (μ_MW - μ_external)
   - Compare to `systematic_corrections_applied.json`

2. **P-L correction**: Recompute from grid
   - Compute P-L span after anchor-demean
   - Calculate P-L correction: -0.5 × span
   - Compare to documented -0.22 km/s/Mpc

3. **Epistemic penalty**: Recompute from first principles
   - Load Δ_T = 1.36, f_systematic = 0.50
   - Compute u_epi = 0.5 × |ΔH| × Δ_T × (1 - f_sys)
   - Compare to ~1.42 km/s/Mpc

4. **Concordance merge**: Independent calculation
   - Apply epistemic penalty to both measurements
   - Perform inverse-variance merge
   - Compare to H₀ = 68.518 ± 1.292 km/s/Mpc

5. **Tension reduction**: Verify claimed reduction
   - Recompute baseline tension (no corrections)
   - Recompute final tension (with corrections)
   - Verify ~77% reduction claim

**Pass Criteria**:
- All recomputed values within 0.01 km/s/Mpc
- All uncertainties within 0.01 km/s/Mpc
- Tension reduction within 1 percentage point

**Failure Mode**:
- Discrepancy > 0.01 → **INVESTIGATE**
- Discrepancy > 0.1 → **FAIL**

---

### Phase III: Data Fidelity Cross-Validation

**Goal**: Verify input data integrity and internal consistency.

**Steps**:
1. **Planck verification**:
   - Load `planck_samples_key_params.npz`
   - Recompute H₀ from ΛCDM chains
   - Verify 67.27 ± 0.60 km/s/Mpc
   - Check correlation structure (ω_b, ω_c, n_s)

2. **SH0ES anchor verification**:
   - Parse `riess_2016_systematic_grid_210.csv`
   - Verify anchor means: MW≈76.1, LMC≈72.3, NGC4258≈72.5
   - Compute anchor spread: ≈3.84 km/s/Mpc
   - Check for outliers or data entry errors

3. **Bootstrap independence**:
   - Re-run bootstrap with different random seeds
   - Verify distributions center consistently
   - Check for seed-dependence artifacts

4. **Sensitivity analysis**:
   - Vary each anchor by ±1σ
   - Verify claimed sensitivities
   - Document any non-linear responses

**Pass Criteria**:
- Planck H₀ matches within 0.1 km/s/Mpc
- Anchor means match within 0.1 km/s/Mpc
- Bootstrap distributions consistent across seeds
- Sensitivities match claimed values

**Failure Mode**:
- Planck mismatch > 0.5 → **CRITICAL**
- Anchor outliers → **INVESTIGATE**
- Seed dependence → **WARN**

---

### Phase IV: Reproducibility Audit

**Goal**: Verify all outputs are reproducible and gates are honestly applied.

**Steps**:
1. **Hash audit**:
   - Compute SHA-256 of every file in `outputs/`
   - Compare to `SHASUMS256.json`
   - Document any mismatches

2. **Gate verification**:
   - Parse `gates.json`
   - Independently verify each gate threshold
   - Recompute pass/fail for each validation
   - Check for post-hoc gate adjustments

3. **Information conservation**:
   - Verify epistemic penalty **reduces** confidence
   - Check: 1/σ²_penalized < 1/σ²_simple
   - Ensure no confidence inflation

4. **Circular logic detection**:
   - Trace data flow for all computations
   - Flag any data reuse (same data in input & calibration)
   - Check correction derivation independence

**Pass Criteria**:
- All hashes match (or differences documented)
- All gates pass when recomputed
- Information conservation holds
- No circular data usage detected

**Failure Mode**:
- Hash mismatch (undocumented) → **INVESTIGATE**
- Gate failure when recomputed → **CRITICAL FAILURE**
- Confidence inflation → **METHODOLOGICAL FAILURE**
- Circular logic → **FATAL FLAW**

---

### Phase V: Independent Re-implementation

**Goal**: Verify results in completely independent implementations.

**Steps**:
1. **R implementation**:
   - Implement concordance merge in R
   - Use same input JSONs
   - Compare outputs to Python version

2. **Julia implementation**:
   - Implement in Julia for numerical precision
   - Use same input JSONs
   - Compare outputs to Python version

3. **C implementation** (paranoid mode):
   - Low-level implementation in C
   - No libraries except standard math
   - Ultimate numerical precision check

4. **Cross-language validation**:
   - All implementations must agree to < 0.01 km/s/Mpc
   - Document any platform/language differences
   - Identify sources of numerical noise

**Pass Criteria**:
- R within 0.01 km/s/Mpc of Python
- Julia within 0.001 km/s/Mpc of Python
- C within machine precision of Julia
- All agree on gate decisions

**Failure Mode**:
- Disagreement > 0.01 → **INVESTIGATE**
- Disagreement > 0.1 → **IMPLEMENTATION ERROR**
- Different gate decisions → **CRITICAL**

---

### Phase VI: External Cosmology Cross-Checks

**Goal**: Verify result is consistent with independent cosmological probes.

**Steps**:
1. **TRGB (Tip of Red Giant Branch)**:
   - Carnegie-Chicago: H₀ = 69.8 ± 1.7 km/s/Mpc
   - Check: Is our 68.52 within 1σ?

2. **ACT (Atacama Cosmology Telescope)**:
   - ACT DR6: H₀ = 67.9 ± 1.5 km/s/Mpc
   - Check: Consistent?

3. **SPT (South Pole Telescope)**:
   - SPT-3G: H₀ = 68.3 ± 1.5 km/s/Mpc
   - Check: Consistent?

4. **BAO (Baryon Acoustic Oscillations)**:
   - DESI/BOSS: H₀ ≈ 68.5 ± 1.2 km/s/Mpc
   - Check: Consistent?

5. **Concordance mapping**:
   - Plot all probes on single chart
   - Verify our result is not an outlier
   - Check for systematic trends

**Pass Criteria**:
- Within 1σ of at least 3 external probes
- Within 2σ of ALL external probes
- No systematic offset detected

**Failure Mode**:
- Outlier from all probes → **METHODOLOGICAL ISSUE**
- Systematic offset → **UNACCOUNTED BIAS**

---

### Phase VII: Audit Report & Archival

**Goal**: Document everything, sign cryptographically, preserve forever.

**Steps**:
1. **Compile audit report**:
   - All validation logs
   - All hash tables
   - All discrepancy logs
   - All plots and comparisons

2. **Provenance diagram**:
   - GraphViz visualization of data flow
   - Color-coded: verified (green), failed (red), warnings (yellow)

3. **Discrepancy log**:
   - Document EVERY difference found
   - No matter how small
   - Include assessment: negligible, investigate, critical

4. **Cryptographic signing**:
   - SHA-256 digest of final report
   - GPG signature (if available)
   - RFC3161 timestamp from external authority
   - Create immutable audit trail

5. **Re-containerization**:
   - Build new container with tag: `h0_rigorous:rent-validated`
   - Include all RENT tools
   - Freeze as reproducible artifact

**Pass Criteria**:
- Complete audit report generated
- All discrepancies documented
- Cryptographic signature valid
- Container builds successfully

**Failure Mode**:
- Incomplete documentation → **UNPUBLISHABLE**

---

## Adversarial Test Suite

Beyond the seven phases, RENT includes **adversarial tests** designed to break the analysis:

### Test 1: Extreme Anchors
- Set MW = 80 km/s/Mpc (5σ high)
- Set all anchors equal
- Set LMC = NGC4258 exactly
- **Expected**: Graceful handling or clear failure
- **Actual**: [RENT fills in]

### Test 2: Extreme Penalties
- Δ_T = 0 (no penalty)
- Δ_T = 10 (massive penalty)
- Δ_T = -1 (nonsensical)
- f_sys = 0, f_sys = 1 (boundary cases)
- **Expected**: Formula handles 0,10,0,1; rejects -1
- **Actual**: [RENT fills in]

### Test 3: Bootstrap Torture
- Run with 10 different random seeds
- Check for seed artifacts
- Test with 10, 100, 1k, 10k iterations
- Verify convergence
- **Expected**: Stable distributions, no artifacts
- **Actual**: [RENT fills in]

### Test 4: Correlation Breaking
- Remove all ΛCDM parameter correlations
- Recompute Planck H₀
- Check sensitivity
- **Expected**: Modest change (correlations weak)
- **Actual**: [RENT fills in]

### Test 5: Known Bias Injection
- Inject +2 km/s/Mpc bias into SH0ES
- Verify corrections detect it
- Inject -1 km/s/Mpc into Planck
- Verify epistemic penalty responds
- **Expected**: Biases detected, corrected
- **Actual**: [RENT fills in]

---

## Execution

```bash
# Run complete RENT protocol
./run_rent.sh

# Run specific phase
./run_rent.sh --phase 2

# Run adversarial tests only
./run_rent.sh --adversarial

# Generate final report
./run_rent.sh --report
```

---

## Pass/Fail Criteria

### PASS (Validated)
- All 7 phases pass
- All adversarial tests handled gracefully
- Discrepancies documented and explained
- External cross-checks consistent

### MARGINAL PASS (Investigate)
- Minor hash mismatches (documented)
- Numerical differences < 0.01 km/s/Mpc
- 1-2 adversarial tests show unexpected behavior
- External probes: within 1-2σ

### FAIL (Not Validated)
- Any critical hash mismatch
- Numerical differences > 0.1 km/s/Mpc
- Gate failures when recomputed
- Circular logic detected
- Outlier from all external probes

### CRITICAL FAILURE (Fundamental Flaw)
- Confidence inflation detected
- Methodological circular reasoning
- Multiple adversarial test failures
- Cannot reproduce core results

---

## Scientific Philosophy

**Standard validation**: "Does it work as claimed?"
**RENT validation**: "Can we break it? If not, why not?"

RENT embodies:
- **Skepticism**: Assume error until proven otherwise
- **Adversarial testing**: Try to find failure modes
- **Independence**: Multiple implementations, languages, datasets
- **Transparency**: Document EVERY discrepancy
- **Permanence**: Cryptographic signing, timestamping

If RENT finds nothing, the claims are **robust**.
If RENT finds issues, we document them **honestly**.

**Either way, we learn the truth.**

---

**RENT Protocol Version**: 1.0
**Maintained by**: HubbleBubble Forensic Validation Team
**License**: MIT (validation tools), CC-BY (documentation)
**Status**: Ready for adversarial deployment
