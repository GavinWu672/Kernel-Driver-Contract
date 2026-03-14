# Kernel Driver Architecture Review Notes

Use this document to capture architecture review outcomes for:

- IRQL-sensitive paths
- pageable versus non-pageable access
- IRP completion ownership
- cleanup / unwind guarantees

If a review changes a driver assumption, also update:

- `KERNEL_DRIVER_CHECKLIST.md`
- `memory/03_decisions.md`
