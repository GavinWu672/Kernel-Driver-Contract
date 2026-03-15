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
| Ground truth | `ground_truth/` | Manually verified function labels (3 drivers, 42 functions) |
| CI | `.gitlab-ci.yml` | Merge gate + full scan + precision regression |
| Pre-commit | `scripts/pre-commit.hook` | Block commit on hard-stop violations |

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

| Family | Files | Extraction | Classification |
|--------|-------|-----------|----------------|
| KMDF (`EVT_WDF_*`) | 2 | 22/22 (100%) | 22/22 (100%) |
| WDM (function-pointer cast) | 2 | 20/20 (100%) | 15/20 (75%) |
| **Aggregate** | **4** | **42/42 (100%)** | **37/42 (88.1%)** |

WDM misclassifications are a documented structural limitation (see STATUS.md § Known false negatives).

---

## Known Limitations (v1)

- **WDM function-pointer cast registration** — `MajorFunction[]` assignment, `PI8042_KEYBOARD_ISR` cast, `PSERVICE_CALLBACK_ROUTINE`, etc. are not detectable by the current header-file registry approach. Requires registration-site tracking for v2.
- **Single-file analysis** — validators operate on per-file payloads; cross-file correctness (e.g., full call-graph IRQL propagation) is out of scope.
- **Real enterprise codebase** — not yet validated on production driver code.
