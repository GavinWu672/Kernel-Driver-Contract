# Memory Layer

## Purpose

This directory stores durable project context for AI-assisted kernel-driver work.

Only confirmed facts, accepted decisions, and validation evidence should be written here.

## Rules

- Do not store guessed values.
- Do not replace formal specs with memory notes.
- If memory conflicts with `AGENTS.md`, `KERNEL_DRIVER_ARCHITECTURE.md`, or `KERNEL_DRIVER_CHECKLIST.md`, the formal documents win.
- Use `FACT_INTAKE.md`, `SOURCE_INVENTORY.md`, and `FACT_INTAKE_WORKSHEET.md` before promoting new driver facts into memory.

## Files

- `00_master_plan.md`
- `01_active_task.md`
- `02_project_facts.md`
- `03_decisions.md`
- `04_validation_log.md`

## Intake Flow

When connecting a real driver repository:

1. collect source artifacts using `FACT_INTAKE.md`
2. record paths in `SOURCE_INVENTORY.md`
3. update `KERNEL_DRIVER_CHECKLIST.md`
4. promote confirmed facts into `memory/02_project_facts.md`
5. record architecture-impacting decisions in `memory/03_decisions.md`
6. record produced evidence in `memory/04_validation_log.md`
