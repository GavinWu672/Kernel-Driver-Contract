# Kernel Driver Safety Rules

## KD-001 - irql-annotation-required

- Driver functions should include explicit IRQL expectations or reviewer-visible IRQL notes.
- Evidence required:
  - irql_annotation_review
- Enforcement:
  - advisory

## KD-002 - no-paged-access-at-dispatch

- Code at `DISPATCH_LEVEL` or above must not rely on paged memory or blocking kernel APIs.
- Evidence required:
  - irql_safety_review
- Enforcement:
  - hard-stop

## KD-003 - irp-no-sync-wait

- IRP completion paths must not use synchronous waits such as `KeWaitForSingleObject`.
- Evidence required:
  - irp_path_review
- Enforcement:
  - hard-stop

## KD-004 - cleanup-path-required

- Any allocation or acquisition path must have a matching cleanup / unwind path.
- Evidence required:
  - cleanup_review
- Enforcement:
  - advisory

## KD-005 - pool-type-explicit

- Pool allocations should make `NonPagedPoolNx` / `PagedPool` intent explicit.
- Evidence required:
  - pool_type_review
- Enforcement:
  - advisory

## KD-006 - sync-primitive-irql

- Synchronization primitives must match the IRQL at which they are acquired.
  - `KMUTEX` / `KeWaitForMutexObject` requires `PASSIVE_LEVEL`; forbidden at `DISPATCH_LEVEL`.
  - `KEVENT` (synchronization) requires `<= APC_LEVEL`.
  - `KSPIN_LOCK` / `KeAcquireSpinLock` is the correct primitive at `DISPATCH_LEVEL`.
  - `EX_PUSH_LOCK` requires `<= APC_LEVEL`.
- Evidence required:
  - sync_primitive_review
- Enforcement:
  - hard-stop

## KD-007 - dpc-isr-nonblocking

- DPC (`KDEFERRED_ROUTINE`) and ISR (`KSERVICE_ROUTINE`) routines run at `DISPATCH_LEVEL`
  or higher and must not call blocking, pageable, or wait-based APIs.
- Evidence required:
  - dpc_isr_review
- Enforcement:
  - hard-stop

## KD-008 - paged-code-annotation

- Functions placed in pageable sections must call `PAGED_CODE()` at entry.
  Functions in non-pageable sections must NOT call `PAGED_CODE()`.
  Pageable sections must be bracketed with `#pragma alloc_text(PAGE, ...)`.
- Evidence required:
  - pageable_section_review
- Enforcement:
  - advisory

## KD-009 - dispatch-routine-registered

- Every IRP major function handled by the driver must be explicitly assigned to
  `DriverObject->MajorFunction[IRP_MJ_*]`.  Unregistered major functions default
  to the framework stub and must not silently accept IRPs.
- Evidence required:
  - dispatch_registration_review
- Enforcement:
  - advisory

## KD-010 - static-analysis-clean

- Driver Verifier, SDV (Static Driver Verifier), and WDK SAL annotation analysis
  must report no new defects on changed code paths.
- Evidence required:
  - static_analysis_output
- Enforcement:
  - hard-stop
