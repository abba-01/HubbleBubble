# RENT SSOT — Rebuild Everything Nothing Trusted

**RENT_SPEC_VERSION**: 1.0.0
**DATE_ISSUED**: 2025-10-18
**AUTHOR**: HubbleBubble Verification Suite
**PRIMARY_OPERATOR**: ma'am

---

## **1. System Goals**

* Ensure total reproducibility of H₀ cross-calibration results.
* Detect and document any deviation between environments, data, or results.
* Maintain zero-trust verification philosophy: *observe and report, never infer.*
* Prevent sudden termination by using a graceful acceptability/discovery tree.

---

## **2. Execution Policy**

| Mode        | Description                                        | Default Action               |
| ----------- | -------------------------------------------------- | ---------------------------- |
| **strict**  | Full reproduction (requires identical environment) | rebuild on major drift       |
| **audit**   | Observational run for differences                  | log all deviations           |
| **dry-run** | Endpoint and hash verification only                | no data mutation             |
| **auto**    | CI-compatible, non-interactive                     | follow policy.json overrides |

---

## **3. Phases**

1. **Phase 1 — Provenance Reconstruction**

   * Verify OS, Python, and package versions.
   * Record environment drift.
   * Do *not* abort automatically; pass control to acceptability tree.

2. **Phase 2 — Re-Execution from Scratch**

   * Check presence of SH0ES CSV and related inputs.
   * Use `discovery_tree` to fetch from endpoint → mirror → local.
   * Continue or skip according to operator policy.

3. **Phase 3 — Data Fidelity Cross-Validation**

   * Validate Planck chains and SH0ES anchors.
   * Confirm data hashes and version numbers.

4. **Phase 4 — Reproducibility Audit**

   * Verify internal file hashes, confirm gate status, produce final log.

5. **Phase 5 — Independent Re-Implementation** *(optional)*

   * Recompute merge formula in R/Julia/C for cross-language validation.

6. **Phase 6 — External Cross-Checks** *(optional)*

   * Compare results to TRGB, ACT, SPT, BAO/DESI datasets.

7. **Phase 7 — Reporting & Archival**

   * Merge all logs into `RENT_AUDIT_REPORT.md`.
   * Timestamp, sign, and archive.

---

## **4. Acceptability Tree Rules**

| Issue Type        | Default Behavior   | Operator Options         |
| ----------------- | ------------------ | ------------------------ |
| environment_minor | log drift          | override / continue      |
| environment_major | prompt rebuild     | rebuild / override       |
| data_missing      | use discovery tree | fetch / skip / abort     |
| hash_mismatch     | verify source      | retry / override / abort |
| logic_error       | stop execution     | abort                    |
| security_flag     | stop & alert       | abort                    |

All operator decisions are written to `outputs/logs/accept_tree_log.json`.

**Implementation**: See `rent/config/policy.json` for complete acceptability tree specification.

---

## **5. Discovery Tree Policy**

File: `rent/config/discovery_tree.json`

Each dataset defines:

```json
{
  "check": "path/to/local/file",
  "sources": ["primary URL", "mirror URL"],
  "local_fallback": "path/to/mirror/local"
}
```

Execution order: **check → primary → mirror → local fallback → prompt.**

All attempts logged to `outputs/logs/discovery_tree.json`.

---

## **6. Required Archive Fallbacks**

All must exist locally for offline operation:

* `assets/planck/*.json, *.npz`
* `assets/vizier/*.csv, *.json`
* `assets/external/*.json`
* `outputs/reproducibility/*`
* `mirrors/*` for Planck, VizieR, TRGB, DESI
* `rent/config/data_endpoints.json`
* `rent/config/discovery_tree.json`
* `rent/config/policy.json`

---

## **7. Logging & Audit Outputs**

| File                                            | Description                  |
| ----------------------------------------------- | ---------------------------- |
| `outputs/logs/rent_validation_report.json`      | Summary of all phase results |
| `outputs/logs/accept_tree_log.json`             | User decisions and overrides |
| `outputs/logs/discovery_tree.json`              | Endpoint attempts            |
| `outputs/reproducibility/RENT_DATA_LEDGER.json` | Complete dataset provenance  |
| `outputs/logs/RENT_AUDIT_REPORT.md`             | Final signed audit report    |

---

## **8. Automation Hooks**

```bash
python rent/run_rent.py --mode strict|audit|dry-run|auto
```

Returns JSON result code:

```json
{
  "status": "PASS",
  "phases": {
    "1": "pass",
    "2": "pass",
    "3": "pass",
    "4": "pass"
  }
}
```

Triggers feedback pipeline in ClaudeCode to:

* Parse logs
* Generate summary diagnostics
* Suggest remediation for failed phases

---

## **9. Success Criteria**

* All required data present or successfully fetched.
* No unresolved major drifts.
* All file hashes verified.
* Audit report generated and signed.

If all true → `RENT VALIDATION: COMPLETE`.
Otherwise → `RENT VALIDATION: ACTION REQUIRED`.

---

## **10. Post-Execution Feedback**

ClaudeCode or equivalent automation shall:

1. Parse the final JSON summary.
2. Annotate failed phases with probable causes.
3. Provide a one-page summary highlighting:

   * Environment integrity
   * Data availability
   * Endpoint health
   * Hash consistency

---

## **Implementation Files**

| File                                  | Purpose                                  |
| ------------------------------------- | ---------------------------------------- |
| `rent/config/policy.json`             | Execution modes and acceptability tree   |
| `rent/config/discovery_tree.json`     | Data fetching hierarchy                  |
| `rent/config/data_endpoints.json`     | External endpoint configurations         |
| `rent/run_rent.py`                    | Master RENT runner                       |
| `rent/lib/acceptability_tree.py`      | Acceptability tree implementation        |
| `rent/lib/discovery_tree.py`          | Data discovery and fetching              |
| `rent/lib/feedback.py`                | Post-execution feedback generator        |
| `outputs/logs/accept_tree_log.json`   | Operator decision log                    |
| `outputs/logs/discovery_tree.json`    | Data fetch attempt log                   |
| `outputs/logs/RENT_AUDIT_REPORT.md`   | Final comprehensive audit report         |
| `outputs/reproducibility/RENT_DATA_LEDGER.json` | Complete dataset provenance ledger |

---

This SSOT is complete and deterministic.

When *ClaudeCode* or any executor reads it, it should:

1. Load configuration files per sections 4–5.
2. Execute all implemented phases sequentially.
3. Produce all logs listed in section 7.
4. Deliver feedback and remediation hints as per section 10.

---

**End of SSOT — RENT_SPEC_VERSION 1.0.0**
