# Microsoft Driver Verification Standards — Coverage Mapping

> Version: 1.1 — 2026-03-16
> Scope: Kernel Driver Contract v1 (KMDF-first policy checker)
> Purpose: Intent-based traceability reference against Microsoft's driver verification stack. Not a WHCP/WHQL readiness substitute. Not certification evidence. Not a claim of equivalence to DV, SDV, or HLK.

---

## Overview

Microsoft's driver verification stack has four main layers:

| Layer | Tool | When it runs | What it catches |
|-------|------|-------------|-----------------|
| 1 | WDK SAL / PREfast | Build time | IRQL annotations, null deref, type misuse |
| 2 | Static Driver Verifier (SDV) | Developer workstation / CI | Reachability across call graphs, locking order, DDI sequencing |
| 3 | Driver Verifier (DV) | Runtime (test machine) | Memory corruption, IRQL violations, deadlocks, IRP misuse |
| 4 | HLK / WHCP test suite | Certification lab | Device functionality, power, PnP, compatibility on target hardware |

**This tool (Kernel Driver Contract)** operates between layers 1 and 2 — as a pre-merge static pattern checker. It does not replace any of the four layers. Its value is catching a well-defined subset of issues at the lowest-cost point: before a change is merged.

### Traceability semantics

The coverage column in all tables below uses the following meanings:

| Symbol | Meaning |
|--------|---------|
| **Yes** | The validator directly checks a substantial portion of the rule intent within the current source file and callback context model, without requiring path sensitivity, inter-procedural flow, or IRQL state tracking. |
| **Partial** | The validator approximates part of the rule intent. Limitations apply: no path sensitivity, no cross-function IRQL propagation, no object lifecycle tracking, and/or coverage is restricted to a subset of the API family named in the rule. |
| **Not covered** | No explicit validator support exists in v1. |

**Rule mapping in this document is intent-based traceability, not a claim of functional equivalence to SDV, Driver Verifier, HLK, or WHCP.**

### Dispatch classification note

In this document, "dispatch" refers to the tool's operational classification bucket for non-ISR / non-DPC callback contexts. It is not a full Microsoft IRQL semantic model. The classifier uses EVT_WDF_* type registry and structural heuristics — it does not implement an IRQL state machine or inter-procedural context propagation.

---

## Microsoft rule intent mapping (approximate)

### IRQL Rules — Driver Verifier DDI Compliance

### IRQL Rules

| Driver Verifier Rule | Description | Our Validator | Coverage |
|---------------------|-------------|---------------|----------|
| `IrqlExAllocatePool` | `ExAllocatePool*` must be called at `IRQL <= DISPATCH_LEVEL`; requires NonPagedPool at DISPATCH | `irql_safety_validator.py` (KD-002) | **Partial** — checks `ExAllocatePoolWithTag` call in dispatch-level functions; does not track IRQL flow across call chains |
| `IrqlExPassive` | Several Ex* routines require `PASSIVE_LEVEL` | `irql_safety_validator.py` (KD-002) | **Partial** — `ZwCreateFile`, `ZwQueryInformationFile` flagged in dispatch context |
| `IrqlExApcLte1–3` | Ex*Push/Pop routines require `IRQL <= APC_LEVEL` | — | **Not covered** |
| `IrqlIoApcLte` | Several Io* routines require `IRQL <= APC_LEVEL` | — | **Not covered** |
| `IrqlIoPassive1–5` | Io* routines requiring `PASSIVE_LEVEL` (IoCreateDevice, IoDeleteDevice, etc.) | `irql_safety_validator.py` (KD-002) | **Partial** — `IoCreateDevice` flagged; `IoDeleteDevice`/`IoDetachDevice` not currently in blocklist |
| `IrqlKeDispatchLte` | Ke* routines requiring `IRQL <= DISPATCH_LEVEL` | — | **Not covered** (e.g. `KeInsertQueueDpc`, `KeSetEvent` with Wait=FALSE) |
| `IrqlKeApcLte1` | `KeWaitForSingleObject`/`KeWaitForMultipleObjects` require `IRQL <= APC_LEVEL` | `irql_safety_validator.py` (KD-002, KD-003) | **Partial** — `KeWaitForSingleObject` flagged in ISR/DPC/dispatch context via API blocklist; `KeWaitForMultipleObjects` not in blocklist; relies on callback classification, not an IRQL state machine |
| `IrqlKeApcLte2` | `KeReleaseMutex`/`KeWaitForMutexObject` require `IRQL <= APC_LEVEL` | — | **Not covered** |
| `IrqlKeReleaseSpinLock` | `KeReleaseSpinLock` must restore IRQL to value from acquire | `sync_primitive_validator.py` (KD-006–KD-008) | **Partial** — unpaired release detected; IRQL value tracking not implemented |
| `IrqlMmApcLte` | `MmProbeAndLockPages` requires `IRQL <= APC_LEVEL` | — | **Not covered** |
| `IrqlObPassive` | `ObReferenceObjectByHandle` requires `PASSIVE_LEVEL` | — | **Not covered** |
| `IrqlPsPassive` | Ps* routines require `PASSIVE_LEVEL` | — | **Not covered** |
| `IrqlRtlPassive` | Several Rtl* routines require `PASSIVE_LEVEL` | — | **Not covered** |
| `IrqlZwPassive` | Zw* routines require `PASSIVE_LEVEL` | `irql_safety_validator.py` (KD-002) | **Partial** — `ZwCreateFile`, `ZwQueryInformationFile` covered; broader Zw* family not enumerated |
| `IrqlReturn` | ISR must preserve and restore IRQL correctly | `irql_safety_validator.py` (KD-001) | **Partial** — ISR/DPC classification-based flagging; actual IRQL state machine not tracked |

### Locking / Synchronization Rules

| Driver Verifier Rule | Description | Our Validator | Coverage |
|---------------------|-------------|---------------|----------|
| `SpinLock` | SpinLock acquire/release must be balanced; no double-acquire | `sync_primitive_validator.py` (KD-006) | **Partial** — structural pattern check; cross-function flow not tracked |
| `QueuedSpinLock` | Same for queued spinlocks | `sync_primitive_validator.py` (KD-006) | **Partial** — same limitation |
| `SpinLockSafe` | No `KeAcquireSpinLock` at `IRQL > DISPATCH_LEVEL` | `sync_primitive_validator.py` (KD-007) | **Partial** — ISR/DPC context detection; not a full IRQL tracker |
| `CancelSpinLock` | Balanced acquire/release of cancel spinlock | — | **Not covered** |
| `IrpProcessing` | IRP completion rules | — | **Not covered** (out of v1 scope) |

### Pool Allocation Rules

| Driver Verifier Rule | Description | Our Validator | Coverage |
|---------------------|-------------|---------------|----------|
| `IrqlExAllocatePool` (pool type) | Must use NonPagedPool at `DISPATCH_LEVEL` | `pool_type_validator.py` (KD-004, KD-005) | **Partial** — PagedPool in non-pageable context detected via callback classification; relies on non-pageable context label, not runtime IRQL tracking |
| Pool tagging | `ExAllocatePoolWithTag` preferred over untagged allocations | `pool_type_validator.py` | **Partial** — untagged `ExAllocatePool` flagged as advisory |
| Special Pool / Guard Pages | Detect use-after-free, buffer overrun via guard allocations | — | **Not covered** — runtime only (Driver Verifier special pool mode) |

---

## SDV rule intent mapping (approximate)

### KMDF Locking Rules — SDV

| SDV Rule | Description | Our Validator | Coverage |
|----------|-------------|---------------|----------|
| `WdfSpinlock` | `WdfSpinLockAcquire` must be released before callback returns | `sync_primitive_validator.py` (KD-006) | **Partial** — pattern-based; no inter-procedural flow |
| `WdfInterruptLock` | `WdfInterruptAcquireLock` / `WdfInterruptReleaseLock` must be balanced | `sync_primitive_validator.py` (KD-008) | **Partial** |
| `ReqSendWhileSpinlock` | Must not call `WdfRequestSend` while spinlock held | `sync_primitive_validator.py` (KD-007) | **Partial** — `WdfRequestSend` in spinlock-held context flagged within a single function body; inter-function spinlock propagation not tracked |
| `DoubleDeviceInitFree` | `WdfDeviceInitFree` called twice on same object | — | **Not covered** |
| `EvtIoStopResume` | `EvtIoStop` must either requeue or complete the request | — | **Not covered** |
| `KmdfIrql` | All KMDF callbacks must be called at documented IRQL | `irql_safety_validator.py` (KD-001) | **Partial** — covers ISR (DIRQL), DPC (DISPATCH_LEVEL), dispatch callbacks (PASSIVE_LEVEL expected) |
| `KmdfIrql2` | No paged APIs callable from dispatch-level KMDF callbacks | `irql_safety_validator.py` (KD-002) | **Partial** — covers listed paged API set |

### WDM DDI Usage Rules — SDV

| SDV Rule | Description | Our Validator | Coverage |
|----------|-------------|---------------|----------|
| `CancelRoutine` | Cancel routine must be set/cleared safely | — | **Not covered** |
| `CompletionRoutine` | IRP completion routines must call IoCompleteRequest | — | **Not covered** — KD-009 checks structural handler presence, not IRP semantic correctness; claiming coverage here would overstate capability |
| `ForwardedAtBadIrql` | IRP forwarded at wrong IRQL | — | **Not covered** |
| `IrpProcessingComplete` | IRP must be completed or forwarded | — | **Not covered** |
| `RemoveLockCheck` | Remove lock must be acquired before accessing device | — | **Not covered** |
| `StartDeviceWait` | KeWaitForSingleObject not allowed in StartDevice at PASSIVE_LEVEL with kernel wait | — | **Not covered** |

---

## SAL / PREfast IRQL Annotations — handling

| SAL Annotation | Meaning | How we handle it |
|----------------|---------|-----------------|
| `_IRQL_requires_max_(DISPATCH_LEVEL)` | Function must not be called above DISPATCH_LEVEL | `irql_safety_validator.py` — used as classification signal for dispatch-safe context |
| `_IRQL_requires_(PASSIVE_LEVEL)` | Function requires PASSIVE_LEVEL | `irql_safety_validator.py` — `_IRQL_requires_` annotations parsed to detect violations in higher-IRQL callers |
| `_IRQL_requires_(DISPATCH_LEVEL)` | Function requires DISPATCH_LEVEL | `dpc_isr_validator.py` (KD-003) — DPC callback IRQL constraint |
| `_IRQL_raises_(DISPATCH_LEVEL)` | Function raises IRQL | `sync_primitive_validator.py` — spinlock acquire detection |
| `_IRQL_saves_` / `_IRQL_restores_` | IRQL is saved/restored by this function | **Not tracked** — we do not model IRQL state across calls |
| `_IRQL_requires_same_` | Caller IRQL must be preserved on return | **Not tracked** |
| `__drv_requiresIRQL` | Legacy annotation (PREfast) | **Not tracked** |

**Gap note:** We detect SAL annotation presence as a classification hint, but we do not implement an IRQL state machine. Cross-function IRQL propagation analysis belongs to PREfast/SDV.

---

## Pageable Section Rules — coverage

| WDK Requirement | Description | Our Validator | Coverage |
|-----------------|-------------|---------------|----------|
| `PAGED_CODE()` macro in pageable functions | Must assert PASSIVE_LEVEL before any paged access | `pageable_section_validator.py` (KD-010) | **Partial** — `#pragma alloc_text(PAGE, ...)` functions checked for `PAGED_CODE()` presence; does not verify that paged code is actually only reachable at PASSIVE_LEVEL |
| No locking primitives in paged code | Pageable functions must not acquire spinlocks | `pageable_section_validator.py` (KD-010) | **Partial** — flagged when spinlock acquire found in PAGE-allocated function |
| Pageable code not callable from DPC/ISR | `#pragma alloc_text(PAGE, ...)` functions must not be reached from DISPATCH_LEVEL | `pageable_section_validator.py` (KD-010) + `dpc_isr_validator.py` | **Partial** — direct call detection; not full call-graph reachability |

---

## HLK / WHCP Test Categories — Relevance Assessment

| HLK Test Category | What it tests | Our tool's relevance |
|-------------------|---------------|----------------------|
| **Device Fundamentals — Reliability** | PnP add/remove/rebalance, surprise remove, disable/enable | **Indirect** — dispatch routine completeness (KD-009) catches missing IRP handlers; we do not test actual PnP state machine |
| **Device Fundamentals — I/O** | I/O stress, concurrent I/O, cancel I/O | **None** — runtime behavior; not amenable to static pattern checking |
| **Device Fundamentals — Power Management** | Sleep/resume, D-state transitions, driver power policy | **None** — runtime behavior |
| **Driver Verifier enabled runs** | All HLK tests run with DV enabled (Standard + DDI Compliance rule sets) | **Complementary** — our pre-merge checks reduce DV failures by catching a subset of DDI compliance violations before they reach the test lab |
| **Static Tools** | SDV / Code Analysis (CA) results required for certification | **Complementary** — our checks add a merge-gate layer; SDV/CA remain required by WHCP |
| **Windows Security** | Driver signing, kernel attestation | **None** — outside static code analysis scope |

---

## Coverage Summary

### What this tool covers (pre-merge static pattern matching)

- IRQL violation patterns at ISR, DPC, dispatch callback boundaries (KD-001 through KD-003)
- Pool type misuse: paged allocation in non-pageable context (KD-004, KD-005)
- Spinlock/interrupt lock acquire–release imbalance within a single function body (KD-006 through KD-008)
- Dispatch routine completeness: required IRP major functions present (KD-009)
- Pageable section annotation discipline: `PAGED_CODE()` presence, spinlock in paged function (KD-010)
- Callback role classification: ISR / DPC / dispatch / other (for the above rules to apply correctly)

### What this tool does NOT cover (by design)

| Gap category | Examples | Why not in scope |
|-------------|----------|-----------------|
| Runtime memory safety | Special pool, use-after-free, buffer overrun | Requires runtime instrumentation (Driver Verifier Special Pool mode) |
| IRP lifecycle | Cancel routine safety, completion routine correctness, IRP stack location tracking | Requires inter-procedural dataflow / symbolic execution |
| IRQL state machine | Cross-function IRQL propagation, `_IRQL_saves_`/`_IRQL_restores_` modeling | Requires abstract interpretation (SDV / PREfast level) |
| Power management | D-state transitions, `PoRequestPowerIrp`, `PoStartNextPowerIrp` sequencing | Runtime + PnP state machine analysis |
| Deadlock detection | Lock order violations across multiple threads | Requires dynamic analysis (Driver Verifier Deadlock Detection) |
| Security checks | Token manipulation, privilege escalation patterns | Requires semantic analysis beyond pattern matching |
| DMA / DPC object lifecycle | DMA adapter release ordering, DPC object re-use | Runtime + object lifecycle tracking |
| WDM function-pointer registration | `MajorFunction[]`, `PI8042_KEYBOARD_ISR` cast patterns | Requires registration-site tracking or AST (v2 work item) |

---

## Design Rationale: Pre-merge Checks vs. DV/SDV/HLK

```
Developer writes code
        │
        ▼
[Kernel Driver Contract — pre-merge]  ← this tool
  Pattern-match IRQL boundaries
  Pool type / spinlock discipline
  Pageable section annotation
  Dispatch completeness
        │ catches subset early, at merge-gate cost
        ▼
[WDK PREfast / Code Analysis — build time]
  SAL annotation flow
  Broader DDI type checking
        │
        ▼
[Static Driver Verifier — developer CI]
  Full DDI compliance rule sets
  Inter-procedural reachability
        │
        ▼
[Driver Verifier — runtime test machine]
  Runtime IRQL tracking
  Memory corruption detection
  Deadlock detection
  IRP lifecycle enforcement
        │
        ▼
[HLK / WHCP certification lab]
  Hardware compatibility
  Power management
  All DV rule sets enabled
  Device Fundamentals reliability/I/O
```

**The value of this tool is not coverage breadth — it is cost.** A Driver Verifier IRQL violation discovered during HLK certification costs significantly more to fix than one caught at merge time. This tool targets the highest-signal, lowest-false-positive subset of Driver Verifier's DDI Compliance rules that can be detected from source text without an IRQL state machine.

---

## Validator → Driver Verifier Rule Traceability Index

| Our Rule ID | Validator file | Primary DV/SDV rules covered | Primary SAL annotations |
|-------------|---------------|------------------------------|------------------------|
| KD-001 | `irql_safety_validator.py` | `IrqlReturn` (partial), `KmdfIrql` (partial) | `_IRQL_requires_(DISPATCH_LEVEL)`, `_IRQL_requires_(HIGH_LEVEL)` |
| KD-002 | `irql_safety_validator.py` | `IrqlExAllocatePool` (partial), `IrqlExPassive` (partial), `IrqlZwPassive` (partial), `IrqlIoPassive1` (partial), `IrqlKeApcLte1` (partial) | `_IRQL_requires_max_(PASSIVE_LEVEL)`, `_IRQL_requires_(PASSIVE_LEVEL)` |
| KD-003 | `dpc_isr_validator.py` | `IrqlKeApcLte1`, `KmdfIrql2` (partial) | `_IRQL_requires_(DISPATCH_LEVEL)` |
| KD-004 | `pool_type_validator.py` | `IrqlExAllocatePool` (pool type variant) | — |
| KD-005 | `pool_type_validator.py` | `IrqlExAllocatePool` (pool type variant) | — |
| KD-006 | `sync_primitive_validator.py` | `SpinLock`, `QueuedSpinLock`, `WdfSpinlock` (partial) | `_IRQL_raises_(DISPATCH_LEVEL)`, `_IRQL_saves_` |
| KD-007 | `sync_primitive_validator.py` | `SpinLockSafe`, `ReqSendWhileSpinlock` | — |
| KD-008 | `sync_primitive_validator.py` | `WdfInterruptLock` (partial) | — |
| KD-009 | `dispatch_routine_validator.py` | Structural precondition only: required `IRP_MJ_*` handler presence. Does not approximate `IrpProcessingComplete` or `CompletionRoutine` semantics. | — |
| KD-010 | `pageable_section_validator.py` | `IrqlExPassive` (paged code variant) | `_IRQL_requires_(PASSIVE_LEVEL)` (implicit via `PAGED_CODE()`) |

---

## References

- [Driver Verifier DDI Compliance Rules](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/ddi-compliance-checking)
- [Static Driver Verifier Rule Sets](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/static-driver-verifier-rule-sets--kmdf-)
- [WDK SAL 2.0 Annotations for Windows Drivers](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/sal-2-annotations-for-windows-drivers)
- [Windows Hardware Lab Kit](https://learn.microsoft.com/en-us/windows-hardware/test/hlk/)
- [WHCP Driver Package Requirements](https://learn.microsoft.com/en-us/windows-hardware/design/compatibility/whcp-specifications-policies)
- [Code Analysis for Drivers Warnings](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/prefast-for-drivers-warnings)
