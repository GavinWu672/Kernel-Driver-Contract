# Kernel Driver Contract

A policy-check prototype for Windows kernel driver code.
Scans real `.c`/`.h` source files, runs rule validators, and enforces hard-stop violations in CI.

**Scope (v1): KMDF-first.**
The scanner reliably classifies KMDF `EVT_WDF_*` callbacks.
WDM function-pointer cast registration is a known structural limitation — see [STATUS.md](STATUS.md).

---

## What This Repo Does

```
source file (.c/.h)
    └─▶ scan_source.py        ← extract functions, classify IRQL context
            └─▶ .checks.json  ← structured payload
                    └─▶ run_validators.py   ← 7 validators, KD-001 to KD-010
                                └─▶ pass / hard-stop violation
```

| Component | File | Purpose |
|-----------|------|---------|
| Scanner | `scan_source.py` | Scan real driver source, emit `.checks.json` |
| Runner | `run_validators.py` | Run all validators against payloads or fixtures |
| Validators | `validators/` | KD-001–KD-010 (IRQL, pool, sync, DPC/ISR, pageable, dispatch, static analysis) |
| Precision tool | `check_precision.py` | Measure extraction coverage + classification accuracy |
| Ground truth | `ground_truth/` | Manually verified function labels (10 files, 111 functions, 4 driver families) |
| CI | `.gitlab-ci.yml` | Merge gate + full scan + precision regression |
| Pre-commit | `scripts/pre-commit.hook` | Block commit on hard-stop violations |
| Standards mapping | `docs/microsoft-standards-mapping.md` | Traceability against Driver Verifier / SDV rule intents |

---

## Quick Start

```bash
# Scan a driver file
python scan_source.py path/to/driver.c --output-dir out/

# Run validators on the output
python run_validators.py out/

# Run fixture self-tests
python run_validators.py fixtures/

# Check classification precision against ground truth
python check_precision.py --batch ground_truth/*.json \
    --wdf-dirs path/to/driver/headers \
    --min-coverage 1.0 --min-accuracy 0.85

# Install pre-commit hook
bash scripts/install-hooks.sh
```

---

## Rules

| ID | Name | Enforcement |
|----|------|-------------|
| KD-001 | irql-aware-api | advisory |
| KD-002 | irql-safe-api | **hard-stop** |
| KD-003 | irql-pool-type | **hard-stop** |
| KD-004–005 | (pool allocation) | advisory |
| KD-006 | sync-primitive-irql | **hard-stop** |
| KD-007 | dpc-isr-nonblocking | **hard-stop** |
| KD-008 | paged-code-annotation | advisory |
| KD-009 | dispatch-routine-registered | advisory |
| KD-010 | static-analysis-clean | **hard-stop** |

---

## Precision Baseline

See [STATUS.md](STATUS.md) for full details.

| Tier | Representative files | Extraction | Classification |
|------|---------------------|-----------|----------------|
| Pure KMDF (`EVT_WDF_*`) | kmdf_fx2 (2 files) | 15/15 (100%) | 15/15 (100%) |
| KMDF + NDIS heritage (explicit spinlocks) | pcidrv (6 files) | 76/76 (100%) | 71/76 (93.4%) |
| WDM function-pointer cast | kbfiltr, cancel (2 files) | 20/20 (100%) | 15/20 (75%) |
| **Aggregate** | **10 files, 4 families** | **111/111 (100%)** | **101/111 (91.0%)** |

WDM misclassifications are a documented structural limitation. In tested samples, spinlock heuristic FP appeared only in the KMDF+NDIS-heritage family. See [STATUS.md](STATUS.md) for the full error inventory.

---

## Pilot Quick Start

For running the first scan on a real driver directory and interpreting results.

**Step 1 — Scan source files**

```bash
python scan_source.py path/to/driver/ --output-dir out/
```

This produces one `.checks.json` per `.c` file. Each file contains extracted functions with their classified roles (`isr`, `dpc`, `dispatch`, `other`) and any detected violation patterns.

**Step 2 — Run validators**

```bash
python run_validators.py out/
```

Output format per file:

```
[PASS]      out/foo.checks.json
[HARD-STOP] out/bar.checks.json  KD-002: KeWaitForSingleObject called in ISR context
```

- `PASS` — no violations detected
- `ADVISORY` — flagged, informational only, does not block
- `HARD-STOP` — would block a merge gate; treat as a real issue to investigate

**Step 3 — Interpret results**

| What you see | What it means |
|--------------|---------------|
| False positive on a helper function | Check if the function is called from a spinlock-held context. If it is a pure helper with no locking semantics, add it to the `other` bucket by confirming it has no `EVT_WDF_*` declaration. |
| ISR classification on a non-ISR callback | Likely a WDM function-pointer cast registration. This is a known v1 structural limitation — see STATUS.md § WDM cast FN. |
| No functions extracted | Confirm the file has standard C function definitions; heavily macro-wrapped functions may not be extracted. |
| High false positive rate on `dispatch` label | If the driver uses legacy explicit spinlock patterns (NDIS-heritage), the spinlock heuristic may fire on helper functions. Document and count before deciding to filter. |

**Step 4 — Measure classification quality (optional)**

If you have time to build a ground truth sample (20–30 functions, manually verified):

```bash
python check_precision.py --batch your_gt.json \
    --wdf-dirs path/to/driver/headers \
    --min-coverage 1.0 --min-accuracy 0.85
```

Expected baseline for a pure KMDF driver: extraction 100%, classification ~100%. Anything below 90% warrants investigation before relying on the validator results.

---

## Known Limitations (v1)

- **WDM function-pointer cast registration** — `MajorFunction[]` assignment, `PI8042_KEYBOARD_ISR` cast, `PSERVICE_CALLBACK_ROUTINE`, etc. are not detectable by the current header-file registry approach. Requires registration-site tracking for v2.
- **Single-file analysis** — validators operate on per-file payloads; cross-file correctness (e.g., full call-graph IRQL propagation) is out of scope.
- **Real enterprise codebase** — not yet validated on production driver code.
