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
