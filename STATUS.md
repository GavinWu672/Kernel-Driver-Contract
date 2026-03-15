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

Measured against manually verified ground truth across 10 files, 4 driver families.

| File | Driver family | GT functions | Extraction | Classification |
|------|--------------|-------------|-----------|----------------|
| `pcidrv/HW/isrdpc.c` | KMDF + NDIS heritage | 11 | 11/11 (100%) | 11/11 (100%) |
| `pcidrv/HW/nic_send.c` | KMDF + NDIS heritage | 11 | 11/11 (100%) | 11/11 (100%) |
| `pcidrv/HW/nic_init.c` | KMDF + NDIS heritage | 23 | 23/23 (100%) | 23/23 (100%) |
| `pcidrv/HW/nic_pm.c` | KMDF + NDIS heritage | 18 | 18/18 (100%) | 16/18 (89%) |
| `pcidrv/HW/nic_recv.c` | KMDF + NDIS heritage | 5 | 5/5 (100%) | 3/5 (60%) |
| `pcidrv/HW/routines.c` | KMDF + NDIS heritage | 8 | 8/8 (100%) | 7/8 (88%) |
| `kbfiltr/sys/kbfiltr.c` | WDM keyboard filter | 8 | 8/8 (100%) | 6/8 (75%) |
| `cancel/sys/cancel.c` | WDM cancel-safe queue | 12 | 12/12 (100%) | 9/12 (75%) |
| `kmdf_fx2/interrupt.c` | KMDF USB (pure) | 3 | 3/3 (100%) | 3/3 (100%) |
| `kmdf_fx2/ioctl.c` | KMDF USB (pure) | 12 | 12/12 (100%) | 12/12 (100%) |
| **Aggregate** | | **111** | **111/111 (100%)** | **101/111 (91.0%)** |

**By driver tier (v1 capability map):**

| Tier | Representative samples | Extraction | Classification |
|------|----------------------|-----------|----------------|
| Pure KMDF (EVT_WDF_*, lock-free) | fx2, vhidmini2\*, usbsamp\* | 100% | ~100% in tested samples |
| KMDF + NDIS heritage (explicit spinlocks) | pcidrv | 100% | 93.2% (5 heuristic FP) |
| WDM function-pointer cast | kbfiltr, cancel | 100% | 75% (structural FN) |

\* vhidmini2 and usbsamp: reconnaissance only, no formal GT. Included to establish spinlock heuristic boundary.

Aggregate per-label (10-file batch):

| Label    | Precision | Recall | Notes |
|----------|-----------|--------|-------|
| dispatch | 1.00 | 0.62 | 3 FN from WDM MajorFunction[] (structural) |
| dpc      | 1.00 | 0.75 | 1 FN from WDM PSERVICE_CALLBACK_ROUTINE (structural) |
| isr      | 1.00 | 0.75 | 1 FN from WDM PI8042_KEYBOARD_ISR (structural) |
| other    | 0.95 | 0.95 | 5 FP from spinlock heuristic; 5 FN from WDM cast |

---

## Known Error Inventory

### WDM cast FN (5) — structural, v2

All share root cause: scanner cannot resolve WDM function-pointer cast registration.

| Function | File | Expected | Got | Pattern |
|----------|------|----------|-----|---------|
| `KbFilter_IsrHook` | kbfiltr.c | isr | other | `(PI8042_KEYBOARD_ISR) func` |
| `KbFilter_ServiceCallback` | kbfiltr.c | dpc | other | struct field assignment |
| `CsampCreateClose` | cancel.c | dispatch | other | `MajorFunction[] = func` |
| `CsampRead` | cancel.c | dispatch | other | `MajorFunction[] = func` |
| `CsampCleanup` | cancel.c | dispatch | other | `MajorFunction[] = func` |

Fix requires registration-site tracking or AST analysis. Out of scope for v1.

### Spinlock heuristic-only FP (5) — scoped v1 limitation

| Function | File | Expected | Got | Trigger |
|----------|------|----------|-----|---------|
| `NICHandleRecvInterrupt` | nic_recv.c | other | dispatch | Helper called with Rcv spinlock held |
| `NICServiceReadIrps` | nic_recv.c | other | dispatch | Caller spinlock context |
| `MPSetPowerD0` | nic_pm.c | other | dispatch | Acquires spinlock internally |
| `NICAddWakeUpPattern` | nic_pm.c | other | dispatch | Acquires spinlock internally |
| `DumpStatsCounters` | routines.c | other | dispatch | WdfSpinLockAcquire in body |

All 5 are in pcidrv, which mixes KMDF callbacks with legacy NDIS-style explicit spinlock management.

---

## Current V1 Boundary: spinlock heuristic FP scope

Sample survey across 4 KMDF drivers:

| Sample | Architecture | Explicit spinlock usage | Heuristic-only FP |
|--------|-------------|------------------------|-------------------|
| pcidrv | KMDF + NDIS heritage | Yes | 5 |
| kmdf_fx2 | Pure KMDF USB | No | 0 |
| vhidmini2 | Pure KMDF HID | No | 0 |
| usbsamp | Pure KMDF USB | No | 0 |

**Current interpretation (tested scope):**

In tested samples, spinlock heuristic-only false positives were observed only in KMDF drivers that retain legacy/NDIS-style explicit spinlock patterns. Tested pure KMDF samples that rely on framework-managed queue serialization did not trigger the spinlock heuristic.

**What this does NOT prove:**
- It does not prove spinlock heuristic FP is impossible in all non-pcidrv KMDF drivers.
- It does not eliminate the structural blind spot for WDM/NDIS function-pointer registration.
- Sample count is small; a KMDF driver with explicit spinlocks outside the NDIS/pcidrv pattern has not been tested.

**Decision impact:**
- Do not modify the spinlock heuristic for v1. Three additional samples confirm zero FP under pure KMDF / framework-serialized architecture.
- Treat current 5 heuristic-only FP as a scoped v1 limitation tied to legacy explicit-spinlock patterns unless new counterexamples appear.
- For real driver repo pilot: prefer a pure KMDF driver to minimize known noise sources.
- Prioritize pilot data collection over heuristic tuning to avoid overfitting to pcidrv-specific helpers.

---

## Strategic Conclusion: KMDF-first v1

v1 capability tiers (evidence-based):

| Tier | Current evidence | Risk profile |
|------|-----------------|-------------|
| **KMDF EVT_WDF_\* family (pure)** | 100% classification in tested samples | Low FP risk confirmed |
| **KMDF + legacy spinlock pattern** | 93.2%; 5 known heuristic FP | Moderate FP risk, documented |
| **WDM function-pointer cast** | 75%; structural blind spot | High FN risk, v2 work |

**Decision: v1 scope = KMDF-first policy checker**

- `MajorFunction[]` and other WDM cast patterns are marked as known structural limitations
- WDM support requires registration-site tracking or AST analysis — out of scope for v1
- Spinlock heuristic is retained as-is; adjustments deferred until counterexample evidence justifies the risk of introducing new FN

---

## What Has NOT Been Proven

- **Behavior on real enterprise codebase.** Naming conventions, macro usage, and registration patterns in production drivers vary from WDK samples.
- **False positive cost in RD workflow.** Signal-to-noise ratio on real code is unmeasured.
- **WDM driver support.** Explicitly out of scope for v1.
- **Spinlock heuristic FP impossibility outside pcidrv-family.** Only tested on 4 KMDF samples.
- **`callback_role_classification` beyond isr/dpc/dispatch/other.** Deeper reasoning out of scope.

---

## Active Known Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| WDM function-pointer cast classification | High / accepted | Structural; v1 is KMDF-first; WDM support is v2 work |
| Spinlock heuristic FP (NDIS-heritage KMDF) | Low / accepted | In tested samples, 5 FP in pcidrv; zero in 3 pure-KMDF samples. Not modifying heuristic without counterexample evidence. |
| `dispatch` recall = 0.62 (aggregate) | WDM-only issue | 100% recall on KMDF dispatch callbacks |
| `dpc`/`isr` recall = 0.75 (aggregate) | WDM-only issue | 100% recall on KMDF dpc/isr callbacks |

---

## Baseline Thresholds (CI regression guard)

```
python check_precision.py --batch ground_truth/*.json \
    --wdf-dirs external/wds2/general/pcidrv/kmdf/HW \
               external/wds2/input/kbfiltr/sys \
               external/wds2/general/cancel/sys \
               external/windows-driver-samples/usb/kmdf_fx2/driver \
               external/windows-driver-samples/usb/kmdf_fx2/inc \
    --min-coverage 1.0 --min-accuracy 0.85
```

| Metric | Pure KMDF (6 files) | Aggregate (10 files) | Minimum enforced |
|--------|--------------------|--------------------|-----------------|
| Extraction coverage | 100.0% | 100.0% | 100.0% |
| Classification accuracy | ~100% | 91.0% | 85.0% |

The 85% floor reflects the known WDM structural gap and pcidrv spinlock FP. The pure KMDF signal (~100%) is the primary quality indicator for v1 targets.

---

## Next Steps (prioritized)

1. **Real driver repo pilot** — controlled scan of one internal pure-KMDF driver; measure FP rate and RD feedback. Prerequisite: KMDF target to stay within proven v1 scope.
2. **Pre-commit hook polish** — packaging and adoption guidance
3. **WDM registration-site tracking (v2)** — requires AST or dataflow analysis; out of scope for v1
