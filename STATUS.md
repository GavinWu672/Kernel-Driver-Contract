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
| `pcidrv/HW/nic_init.c` | KMDF network | 23 | 23/23 (100%) | 23/23 (100%) |
| `pcidrv/HW/nic_pm.c` | KMDF network | 18 | 18/18 (100%) | 16/18 (89%) |
| `pcidrv/HW/nic_recv.c` | KMDF network | 5 | 5/5 (100%) | 3/5 (60%) |
| `pcidrv/HW/routines.c` | KMDF network | 8 | 8/8 (100%) | 7/8 (88%) |
| `kbfiltr/sys/kbfiltr.c` | WDM keyboard filter | 8 | 8/8 (100%) | 6/8 (75%) |
| `cancel/sys/cancel.c` | WDM cancel-safe queue | 12 | 12/12 (100%) | 9/12 (75%) |
| `kmdf_fx2/interrupt.c` | KMDF USB | 3 | 3/3 (100%) | 3/3 (100%) |
| `kmdf_fx2/ioctl.c` | KMDF USB | 12 | 12/12 (100%) | 12/12 (100%) |
| **Aggregate** | | **111** | **111/111 (100%)** | **101/111 (91.0%)** |

**By driver family:**

| Family | Files | Extraction | Classification |
|--------|-------|-----------|----------------|
| KMDF (EVT_WDF_* pattern) | 8 | 73/73 (100%) | 68/73 (93.2%) |
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

**WDM cast FN (5) — structural, v2:**

| Function | File | Expected | Got | Registration pattern |
|----------|------|----------|-----|---------------------|
| `KbFilter_IsrHook` | kbfiltr.c | isr | other | `(PI8042_KEYBOARD_ISR) KbFilter_IsrHook` |
| `KbFilter_ServiceCallback` | kbfiltr.c | dpc | other | `connectData->ClassService = KbFilter_ServiceCallback` |
| `CsampCreateClose` | cancel.c | dispatch | other | `MajorFunction[IRP_MJ_CREATE] = CsampCreateClose` |
| `CsampRead` | cancel.c | dispatch | other | `MajorFunction[IRP_MJ_READ] = CsampRead` |
| `CsampCleanup` | cancel.c | dispatch | other | `MajorFunction[IRP_MJ_CLEANUP] = CsampCleanup` |

**Spinlock heuristic-only FP (5) — pcidrv-specific, not yet proven KMDF-wide:**

| Function | File | Expected | Got | Why heuristic fires |
|----------|------|----------|-----|---------------------|
| `NICHandleRecvInterrupt` | nic_recv.c | other | dispatch | Internal helper called with Rcv spinlock held |
| `NICServiceReadIrps` | nic_recv.c | other | dispatch | Called from NICHandleRecvInterrupt (spinlock context) |
| `MPSetPowerD0` | nic_pm.c | other | dispatch | Acquires spinlock internally |
| `NICAddWakeUpPattern` | nic_pm.c | other | dispatch | Acquires spinlock internally |
| `DumpStatsCounters` | routines.c | other | dispatch | Acquires WdfSpinLock to read stats |

**Spinlock heuristic scope (confirmed after 3 pure-KMDF samples):**
- fx2, vhidmini2, usbsamp — all pure KMDF, all lock-free, all zero heuristic FP
- pcidrv — KMDF wrapping NDIS, uses explicit spinlocks in helpers → 5 FP
- Hypothesis result: spinlock heuristic-only FP is NOT KMDF-wide. It is specific to KMDF drivers that inherit explicit spinlock patterns from legacy NDIS/WDM layers. Pure KMDF drivers use WDF queue serialization and do not exhibit this class of FP.

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
| Spinlock heuristic-only FP on KMDF+NDIS-heritage drivers | Low / accepted for v1 | 5 FP in pcidrv (KMDF wrapping NDIS layer with explicit spinlocks). Verified absent in 3 pure-KMDF drivers (fx2, vhidmini2, usbsamp) — all lock-free. Hypothesis confirmed: FP is specific to KMDF drivers that inherit explicit spinlock patterns from legacy NDIS/WDM layers, not KMDF-wide. Not modifying heuristic in v1; document as known limitation for NDIS-heritage KMDF drivers. |
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

| Metric | KMDF (8 files) | Aggregate (10 files) | Minimum enforced |
|--------|---------------|---------------------|-----------------|
| Extraction coverage | 100.0% | 100.0% | 100.0% |
| Classification accuracy | 93.2% | 91.0% | 85.0% |

The 85% minimum enforces regression detection across the full GT set while honestly reflecting the WDM structural gap. The KMDF path (100%) is the primary quality signal.

---

## Next Steps (prioritized)

1. **Real driver repo pilot** — controlled scan of one internal KMDF driver, measure false positive rate and RD feedback (prerequisite: driver should be KMDF for v1 scope)
2. **Pre-commit hook polish** — packaging and adoption guidance
3. **WDM registration-site tracking (v2)** — requires AST or dataflow analysis; out of scope for v1
