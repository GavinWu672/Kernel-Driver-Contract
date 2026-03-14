> **最後更新**: 2026-03-14
> **Owner**: Kernel Driver Contract
> **Freshness**: Sprint (7d)

# PLAN

[>] Phase 1 : Establish ai-governance-framework integration seam
- Add `contract.yaml`
- Add kernel-driver domain documents
- Add external `kernel-driver` rule pack
- Add advisory IRQL safety validator
- Verify contract loading, session start, and pre-task rule activation

[ ] Phase 2 : Connect to a real driver repository
- Confirm driver model, target OS, and IRQL facts
- Confirm pool allocation and cleanup patterns
- Confirm verifier / SDV / WDK evidence paths

[ ] Phase 3 : Refine kernel-driver evidence routing
- Define dispatch-level code evidence shape
- Add richer IRQL / locking / IRP path validators
