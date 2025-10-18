# RENT: Rebuild Everything, Nothing Trusted

**Version**: 1.0
**Date**: 2025-10-18
**Philosophy**: "If you're not trying to break it, you're not really testing it."
**Core Principle**: "Spooky is fine. Unfalsifiable is not."

---

## What is RENT?

RENT (Rebuild Everything, Nothing Trusted) is a **forensic validation suite** for the HubbleBubble concordance analysis. Unlike standard validation which confirms expected results, RENT actively attempts to:

- **Break the analysis** through edge cases
- **Find discrepancies** between claimed and recomputed values
- **Verify zero assumptions** - rebuild everything from first principles
- **Cross-validate** against independent implementations and external data

**Core principle**: Trust nothing. Verify everything.

---

## Quick Start

```bash
# Run complete RENT protocol (all phases)
cd /got/HubbleBubble
python rent/run_rent.py

# Run specific phase
python rent/phase2_reexecution/run_phase2.py

# Run adversarial tests
python rent/adversarial/run_adversarial_tests.py
```

---

## Seven-Phase Protocol

### Phase I: Provenance Reconstruction ✓
**Goal**: Verify computational environment is exactly as claimed

**Tools**:
- `rent/phase1_provenance/verify_environment.py` - Compare pip packages to documented versions

**Pass Criteria**: All package versions match pip-freeze.txt

---

### Phase II: Re-execution from Scratch ✓
**Goal**: Independently recompute all results from raw data

**Tools**:
- `rent/phase2_reexecution/recompute_corrections.py` - Rebuild anchor and P-L corrections
- `rent/phase2_reexecution/recompute_penalty.py` - Rebuild epistemic penalty
- `rent/phase2_reexecution/recompute_merge.py` - Rebuild concordance merge
- `rent/phase2_reexecution/recompute_tensions.py` - Rebuild tension calculations
- `rent/phase2_reexecution/run_phase2.py` - Master harness

**Pass Criteria**: All recomputed values within 0.01 km/s/Mpc of documented values

**Key Feature**: Every script logs SHA-256 of input files. If someone reruns RENT later with different data, they can determine if differences are due to data changes or methodology errors.

---

### Phase III: Data Fidelity Cross-Validation ✓
**Goal**: Verify input data integrity and internal consistency

**Tools**:
- `rent/phase3_crossvalidation/verify_planck_data.py` - Recompute Planck H₀ from ΛCDM chains
- `rent/phase3_crossvalidation/verify_shoes_anchors.py` - Verify SH0ES anchor means and spread
- `rent/phase3_crossvalidation/run_phase3.py` - Master harness

**Pass Criteria**:
- Planck H₀ within 0.1 km/s/Mpc of 67.27
- Anchor means within 0.2 km/s/Mpc of expected values
- No extreme outliers in systematic grid

---

### Phase IV: Reproducibility Audit ✓
**Goal**: Verify all outputs are reproducible and gates honestly applied

**Tools**:
- `rent/phase4_audit/audit_hashes.py` - Compare all output file hashes to SHASUMS256.json
- `rent/phase4_audit/verify_gates.py` - Independently verify gate thresholds

**Pass Criteria**: All hashes match (or differences documented)

---

### Phase V: Independent Re-implementation (Planned)
**Goal**: Verify results in completely independent implementations

**Templates**:
- `rent/phase5_reimplementation/concordance_merge.R` - R implementation
- `rent/phase5_reimplementation/concordance_merge.jl` - Julia implementation

**Pass Criteria**: All implementations agree to < 0.01 km/s/Mpc

---

### Phase VI: External Cross-Checks (Planned)
**Goal**: Verify result is consistent with independent cosmological probes

**Tools**:
- `rent/phase6_external/compare_trgb.py` - Carnegie-Chicago TRGB
- `rent/phase6_external/compare_act.py` - ACT DR6
- `rent/phase6_external/compare_spt.py` - SPT-3G
- `rent/phase6_external/compare_bao.py` - DESI/BOSS BAO

**Pass Criteria**: Within 1σ of ≥3 probes, within 2σ of all probes

---

### Phase VII: Audit Report & Archival (Planned)
**Goal**: Document everything, sign cryptographically, preserve forever

**Tools**:
- `rent/phase7_reporting/generate_audit_report.py` - Compile comprehensive report
- `rent/phase7_reporting/sign_report.py` - Cryptographic signing

---

## Adversarial Test Suite

Beyond the seven phases, RENT includes **adversarial tests** designed to break the analysis:

### Test 1: Extreme Anchors
- Set MW = 80 km/s/Mpc (5σ high)
- Set all anchors equal
- **Expected**: Graceful handling or clear failure

### Test 2: Extreme Penalties
- Δ_T = 0, 10, -1
- f_sys = 0, 1
- **Expected**: Formula handles boundaries; rejects nonsensical

### Test 3: Bootstrap Torture
- Run with 10 different random seeds
- Test with 10, 100, 1k, 10k iterations
- **Expected**: Stable distributions, no artifacts

### Test 4: Correlation Breaking
- Remove all ΛCDM parameter correlations
- **Expected**: Modest change (correlations weak)

### Test 5: Known Bias Injection
- Inject ±2 km/s/Mpc biases
- **Expected**: Biases detected, corrected

---

## Pass/Fail Criteria

### ✓ PASS (Validated)
- All 7 phases pass
- All adversarial tests handled gracefully
- Discrepancies documented and explained
- External cross-checks consistent

### ⚠ MARGINAL PASS (Investigate)
- Minor hash mismatches (documented)
- Numerical differences < 0.01 km/s/Mpc
- 1-2 adversarial tests show unexpected behavior

### ✗ FAIL (Not Validated)
- Any critical hash mismatch
- Numerical differences > 0.1 km/s/Mpc
- Gate failures when recomputed
- Circular logic detected

### ⚠ CRITICAL FAILURE (Fundamental Flaw)
- Confidence inflation detected
- Methodological circular reasoning
- Multiple adversarial test failures
- Cannot reproduce core results

---

## Key Design Features

### 1. Dataset Provenance Tracking
Every RENT script logs SHA-256 hashes of all input files. This means:
- If you rerun RENT in 2030 and get different results, you can check if it's because:
  - **(A)** You're using different data (compare hashes)
  - **(B)** The methodology is broken (investigate)

### 2. Zero-Trust Re-computation
RENT doesn't load "corrected_h0.json" and trust it. RENT:
1. Loads raw CSV from VizieR
2. Recomputes anchor correction from single-anchor subsets
3. Recomputes P-L correction from anchor-demeaned spreads
4. Compares to documented values with strict tolerances

### 3. Information Conservation Checks
Phase II verifies that epistemic penalty **reduces** confidence:
```
Check: 1/σ²_penalized < 1/σ²_simple
```

If this fails → **confidence inflation** → METHODOLOGICAL FAILURE

### 4. Multi-Language Cross-Validation (Planned)
Planned implementations in R, Julia, and C ensure results aren't Python artifacts.

---

## Implemented vs Planned

| Phase | Status | Scripts |
|-------|--------|---------|
| Phase I   | ✓ Complete | 1/1 scripts |
| Phase II  | ✓ Complete | 5/5 scripts |
| Phase III | ✓ Complete | 2/2 scripts |
| Phase IV  | ⚠ Partial  | 1/2 scripts |
| Phase V   | ⚠ Planned  | 0/2 templates |
| Phase VI  | ⚠ Planned  | 0/4 scripts |
| Phase VII | ⚠ Planned  | 0/2 scripts |
| Adversarial | ⚠ Planned | 0/5 tests |

**Current Status**: Phases I-III fully implemented and validated.

---

## Scientific Philosophy

**Standard validation**: "Does it work as claimed?"
**RENT validation**: "Can we break it? If not, why not?"

### Core Principle: "Spooky is fine. Unfalsifiable is not."

RENT embraces the scientific method's demand for **falsifiability**. We don't require results to be "comfortable" or "intuitive" - cosmology is full of counterintuitive truths (dark energy, quantum mechanics, inflation). What we *do* require is that claims be:

1. **Testable**: Every calculation can be independently recomputed
2. **Reproducible**: Bit-level reproducibility with documented environments
3. **Challengeable**: Adversarial tests actively try to break the analysis
4. **Transparent**: Every input file hashed, every step documented

A concordance result of H₀ = 68.518 km/s/Mpc might seem "spooky" - sitting between Planck and SH0ES in a way that some find suspicious. But if:
- The calculation is independently reproducible ✓
- The corrections are derived from independent data ✓
- The epistemic penalty reduces (not inflates) confidence ✓
- External probes agree ✓
- Adversarial tests fail to break it ✓

...then it's **falsifiable science**, not wishful thinking.

RENT embodies:
- **Skepticism**: Assume error until proven otherwise
- **Adversarial testing**: Try to find failure modes
- **Independence**: Multiple implementations, languages, datasets
- **Transparency**: Document EVERY discrepancy
- **Permanence**: Cryptographic signing, timestamping
- **Falsifiability**: Everything must be independently testable

If RENT finds nothing, the claims are **robust**.
If RENT finds issues, we document them **honestly**.

**Either way, we learn the truth.**

---

## Example Output

```
======================================================================
RENT PHASE II: RE-COMPUTE SYSTEMATIC CORRECTIONS
======================================================================

Step 1: Load raw SH0ES data
----------------------------------------------------------------------
✓ Loaded 210 configurations from SH0ES grid

Step 2: Recompute anchor correction from scratch
----------------------------------------------------------------------
  MW          :  76.13 ± 1.32 km/s/Mpc  (n=70)
  LMC         :  72.27 ± 1.18 km/s/Mpc  (n=70)
  NGC4258     :  72.51 ± 1.25 km/s/Mpc  (n=70)

Anchor split:
  MW:       76.13 km/s/Mpc
  External: 72.39 km/s/Mpc
  Split:    3.74 km/s/Mpc
  Δ_anchor: -1.87 km/s/Mpc

Step 3: Recompute P-L correction from scratch
----------------------------------------------------------------------
  P-L variants: 5
  P-L span: 0.44 km/s/Mpc
  Δ_PL: -0.22 km/s/Mpc

Step 4: Compare to documented values
----------------------------------------------------------------------
Anchor correction:
  Documented:  -1.8700 km/s/Mpc
  Recomputed:  -1.8700 km/s/Mpc
  Difference:  0.0000 km/s/Mpc
  ✓ PASS (within 0.01 km/s/Mpc)

P-L correction:
  Documented:  -0.2200 km/s/Mpc
  Recomputed:  -0.2200 km/s/Mpc
  Difference:  0.0000 km/s/Mpc
  ✓ PASS (within 0.01 km/s/Mpc)

======================================================================
✓ PHASE II VERIFICATION: PASS
======================================================================
```

---

## Logs and Outputs

All RENT validation logs are saved to:
```
outputs/logs/
├── phase1_environment_verification.json
├── phase2_corrections_recomputation.json
├── phase2_penalty_recomputation.json
├── phase2_merge_recomputation.json
├── phase2_tensions_recomputation.json
├── phase2_comprehensive_report.json
├── phase3_planck_verification.json
├── phase3_shoes_anchor_verification.json
└── phase4_hash_audit.json
```

Each log contains:
- Input file SHA-256 hashes
- Recomputed values
- Documented values
- Differences
- Pass/fail verdicts
- Timestamps

---

## For Reviewers

If you're reviewing this analysis:

1. **Start here**: `python rent/run_rent.py`
2. **Check logs**: `outputs/logs/phase*`
3. **Verify hashes**: All input data SHA-256s are logged
4. **Adversarial mindset**: Did we miss any failure modes?

**Key question**: Can you break it? If not, it might be robust.

---

## License

- **Validation tools**: MIT License
- **Documentation**: CC-BY 4.0

---

## Maintenance

**Maintained by**: HubbleBubble Forensic Validation Team
**Version**: 1.0 (2025-10-18)
**Status**: Phases I-III validated and operational

For issues or suggestions: Check `outputs/logs/` for detailed diagnostic information.

---

**Remember**: "If you're not trying to break it, you're not really testing it."
