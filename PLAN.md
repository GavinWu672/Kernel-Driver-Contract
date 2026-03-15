> **最後更新**: 2026-03-15
> **Owner**: Kernel Driver Contract
> **Freshness**: Sprint (7d)

# PLAN

[x] Phase 1 : Establish ai-governance-framework integration seam
- Add `contract.yaml`
- Add kernel-driver domain documents
- Add external `kernel-driver` rule pack
- Add advisory IRQL safety validator + pool type validator
- Verify contract loading, session start, and pre-task rule activation

[x] Phase 3 : Richer kernel-driver validators and CI runner
- sync_primitive_validator (KD-006, hard-stop): spinlock/mutex/pushlock IRQL mismatch
- dpc_isr_validator (KD-007, hard-stop): blocking APIs in DPC/ISR routines
- pageable_section_validator (KD-008, advisory): PAGED_CODE() annotation correctness
- dispatch_routine_validator (KD-009, advisory): MajorFunction registration gaps
- static_analysis_validator (KD-010, hard-stop): Driver Verifier / SDV / WDK output
- run_validators.py: CI/CD pipeline runner with hard-stop exit-code enforcement
- scan_source.py: scans real *.c/*.h sources, classifies by IRQL context, emits checks.json

[ ] Phase 2 : Connect to a real driver repository
- Confirm driver model, target OS, and IRQL facts
- Confirm pool allocation and cleanup patterns
- Confirm verifier / SDV / WDK evidence paths
- Fill memory/02_project_facts.md with confirmed facts

[ ] Phase 4 : CI/CD integration and GitHub Actions
- Add .github/workflows/kernel-driver-check.yml
- Wire scan_source.py + run_validators.py into PR pipeline
- Add pre-commit hook for local enforcement
