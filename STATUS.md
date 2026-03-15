# Kernel Driver Contract — Project Status

> Last updated: 2026-03-15
> Status: **controlled pilot candidate** — not yet ready for general rollout

---

## What Has Been Proven

### Engineering closure
- `scan_source.py` — scans real `.c`/`.h` kernel driver source files
- `run_validators.py` — standalone CI/CD runner, no external framework needed
- 7 validators covering KD-001 through KD-010 (IRQL, pool, sync, DPC/ISR, pageable section, dispatch routines, static analysis)
- GitLab CI pipeline (merge gate + full-scan on push to main)
- GitHub Actions mirror
- Pre-commit hook

### Precision baseline (scope: `callback_role_classification`)

Measured against manually verified ground truth. Three files across two different driver families.

| File | Driver family | GT functions | Extraction | Classification |
|------|--------------|-------------|-----------|----------------|
| `pcidrv/HW/isrdpc.c` | KMDF network | 11 | 11/11 (100%) | 11/11 (100%) |
| `pcidrv/HW/nic_send.c` | KMDF network | 11 | 11/11 (100%) | 11/11 (100%) |
| `kbfiltr/sys/kbfiltr.c` | WDM keyboard filter | 8 | 8/8 (100%) | 6/8 (75%) |
| **Aggregate** | | **30** | **30/30 (100%)** | **28/30 (93.3%)** |

Aggregate per-label (3-file batch):

| Label    | Precision | Recall |
|----------|-----------|--------|
| dispatch | 1.00 | 1.00 |
| dpc      | 1.00 | 0.75 |
| isr      | 1.00 | 0.75 |
| other    | 0.89 | 1.00 |

### Known false negatives and root causes

| Function | Expected | Got | Root cause |
|----------|----------|-----|-----------|
| `KbFilter_IsrHook` | isr | other | `PI8042_KEYBOARD_ISR` cast — WDM function-pointer pattern, no `EVT_WDF_*` declaration |
| `KbFilter_ServiceCallback` | dpc | other | `PSERVICE_CALLBACK_ROUTINE` cast — same WDM-cast detection gap |

Scanner's WDF registry approach resolves KMDF `EVT_WDF_*` forward declarations across files.
It cannot resolve WDM-style function pointer casts (assigned via struct field or direct pointer).
This is a structural limitation, not a fixable heuristic gap.

---

## What Has NOT Been Proven

- **Generalization beyond these samples.** 93.3% batch accuracy is measured on 3 files from 2 public sample drivers. It does not imply the scanner is correct on an arbitrary driver.
- **Behavior on real enterprise codebase.** Naming conventions, macro usage, and callback registration patterns in production drivers vary significantly from WDK samples.
- **False positive cost in RD workflow.** We have not measured how often validators fire on correct code, nor whether the signal-to-noise ratio is acceptable to developers.
- **`callback_role_classification` coverage beyond isr/dpc/dispatch/other.** Deeper architectural reasoning (stack usage, lock ordering, interrupt affinity) is out of scope.
- **WDM-style cast detection.** `PI8042_KEYBOARD_ISR`, `PSERVICE_CALLBACK_ROUTINE`, and similar registration patterns are not detectable from header-file analysis alone.

---

## Active Known Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| WDM function-pointer cast classification | Medium | Structural; requires dataflow or registration-site analysis to fix |
| dpc/isr recall = 0.75 (kbfiltr) | Known, accepted | Documented in ground truth; not a regression risk for KMDF drivers |
| `dispatch` label heuristic | Low | Current heuristic may over-classify some helpers as dispatch on messy codebases |

---

## Baseline Thresholds (CI regression guard)

Run with:
```
python check_precision.py --batch ground_truth/*.json \
    --wdf-dirs external/wds2/general/pcidrv/kmdf/HW external/wds2/input/kbfiltr/sys \
    --min-coverage 1.0 --min-accuracy 0.90
```

| Metric | Current | Minimum enforced |
|--------|---------|-----------------|
| Extraction coverage | 100.0% | 100.0% |
| Classification accuracy | 93.3% | 90.0% |

The 90% minimum is deliberately below current 93.3% to allow headroom for future ground truth expansion without false CI failures. It will be raised as more evidence accumulates.

---

## Next Steps (prioritized)

1. **Expand ground truth** — add a third driver family (e.g., WDM storage or USB) to test generalization further
2. **Real driver repo pilot** — controlled scan of one internal driver, measure false positive rate and RD feedback
3. **Pre-commit hook polish** — currently functional; needs packaging and adoption guidance
4. **WDM-cast detection** — research feasibility; may require AST-level analysis
