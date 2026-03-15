# Kernel Driver Contract — Project Status

> Last updated: 2026-03-15
> Status: **controlled pilot candidate — KMDF-first v1**

---

## What Has Been Proven

### Engineering closure
- `scan_source.py` — scans real `.c`/`.h` kernel driver source files
- `run_validators.py` — standalone CI/CD runner, no external framework needed
- 7 validators covering KD-001 through KD-010 (IRQL, pool, sync, DPC/ISR, pageable section, dispatch routines, static analysis)
- GitLab CI pipeline (merge gate + full-scan on push to main + precision regression gate)
- GitHub Actions mirror
- Pre-commit hook

### Precision baseline (scope: `callback_role_classification`)

Measured against manually verified ground truth. Four files across three different driver families.

| File | Driver family | GT functions | Extraction | Classification |
|------|--------------|-------------|-----------|----------------|
| `pcidrv/HW/isrdpc.c` | KMDF network | 11 | 11/11 (100%) | 11/11 (100%) |
| `pcidrv/HW/nic_send.c` | KMDF network | 11 | 11/11 (100%) | 11/11 (100%) |
| `kbfiltr/sys/kbfiltr.c` | WDM keyboard filter | 8 | 8/8 (100%) | 6/8 (75%) |
| `cancel/sys/cancel.c` | WDM cancel-safe queue | 12 | 12/12 (100%) | 9/12 (75%) |
| **Aggregate** | | **42** | **42/42 (100%)** | **37/42 (88.1%)** |

**By driver family:**

| Family | Files | Extraction | Classification |
|--------|-------|-----------|----------------|
| KMDF (EVT_WDF_* pattern) | 2 | 22/22 (100%) | 22/22 (100%) |
| WDM (function-pointer cast) | 2 | 20/20 (100%) | 15/20 (75%) |

Aggregate per-label (4-file batch):

| Label    | Precision | Recall | Notes |
|----------|-----------|--------|-------|
| dispatch | 1.00 | 0.62 | 3 FN: WDM MajorFunction[] registration not tracked |
| dpc      | 1.00 | 0.75 | 1 FN: PSERVICE_CALLBACK_ROUTINE cast not tracked |
| isr      | 1.00 | 0.75 | 1 FN: PI8042_KEYBOARD_ISR cast not tracked |
| other    | 0.84 | 1.00 | |

### Known false negatives and root causes

All 5 false negatives share the same root cause: **WDM function-pointer cast registration**.

| Function | File | Expected | Got | Registration pattern |
|----------|------|----------|-----|---------------------|
| `KbFilter_IsrHook` | kbfiltr.c | isr | other | `(PI8042_KEYBOARD_ISR) KbFilter_IsrHook` |
| `KbFilter_ServiceCallback` | kbfiltr.c | dpc | other | `connectData->ClassService = KbFilter_ServiceCallback` |
| `CsampCreateClose` | cancel.c | dispatch | other | `MajorFunction[IRP_MJ_CREATE] = CsampCreateClose` |
| `CsampRead` | cancel.c | dispatch | other | `MajorFunction[IRP_MJ_READ] = CsampRead` |
| `CsampCleanup` | cancel.c | dispatch | other | `MajorFunction[IRP_MJ_CLEANUP] = CsampCleanup` |

**Scanner's WDF registry approach resolves KMDF `EVT_WDF_*` forward declarations across files.
It cannot resolve WDM-style function pointer casts or `MajorFunction[]` struct-field assignments.**
This is a structural limitation requiring registration-site dataflow analysis to fix.

---

## Strategic Conclusion: KMDF-first v1

Three samples confirmed KMDF detection is complete; two samples confirmed WDM function-pointer cast is a universal blind spot (not kbfiltr-specific):

| Claim | Evidence |
|-------|---------|
| KMDF EVT_WDF_* callbacks classified correctly | 22/22 across 2 files, 0 false negatives |
| WDM function-pointer cast callbacks misclassified | 5/5 false negatives, 2 files, 2 different cast patterns |

**Decision: v1 scope = KMDF-first policy checker**

- `MajorFunction[]` and other WDM cast patterns are marked as known limitations
- WDM support requires a new analysis layer (registration-site tracking or AST analysis)
- Attempting to patch this with heuristics would create fragile special-cases and false precision

---

## What Has NOT Been Proven

- **Behavior on real enterprise codebase.** Naming conventions, macro usage, and registration patterns in production drivers vary from WDK samples.
- **False positive cost in RD workflow.** Signal-to-noise ratio on real code is unmeasured.
- **WDM driver support.** Explicitly out of scope for v1.
- **`callback_role_classification` coverage beyond isr/dpc/dispatch/other.** Deeper reasoning (stack usage, lock ordering, interrupt affinity) is out of scope.

---

## Active Known Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| WDM function-pointer cast classification | High / accepted | Structural; v1 is KMDF-first; WDM support is v2 work |
| `dispatch` recall = 0.62 (aggregate) | Known, accepted for WDM | 100% on KMDF; WDM MajorFunction[] is out-of-scope for v1 |
| `dpc`/`isr` recall = 0.75 (aggregate) | Known, accepted for WDM | 100% on KMDF; WDM cast gap documented |

---

## Baseline Thresholds (CI regression guard)

Run with:
```
python check_precision.py --batch ground_truth/*.json \
    --wdf-dirs external/wds2/general/pcidrv/kmdf/HW external/wds2/input/kbfiltr/sys \
    --min-coverage 1.0 --min-accuracy 0.85
```

| Metric | KMDF only | Aggregate (all 4 files) | Minimum enforced |
|--------|-----------|------------------------|-----------------|
| Extraction coverage | 100.0% | 100.0% | 100.0% |
| Classification accuracy | 100.0% | 88.1% | 85.0% |

The 85% minimum enforces regression detection across the full GT set while honestly reflecting the WDM structural gap. The KMDF path (100%) is the primary quality signal.

---

## Next Steps (prioritized)

1. **Real driver repo pilot** — controlled scan of one internal KMDF driver, measure false positive rate and RD feedback (prerequisite: driver should be KMDF for v1 scope)
2. **Pre-commit hook polish** — packaging and adoption guidance
3. **WDM registration-site tracking (v2)** — requires AST or dataflow analysis; out of scope for v1
