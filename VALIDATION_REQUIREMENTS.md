# Validation Requirements

This document lists the minimum validation expectations currently supported by this contract repository.

## Current Validation Layers

The current kernel-driver governance loop has four layers:

1. contract loading
2. session bootstrap and validator preflight
3. pre-task rule activation
4. post-task advisory validation

## Minimum Supported Inputs

The repository currently supports validation through:

- `contract.yaml`
- markdown governance documents
- rule files under `rules/kernel-driver/`
- validator scripts under `validators/`
- fixture-style `checks.json` payloads
- patch or code-snippet evidence routed through framework post-task checks

## Required Baseline Verifications

The following checks should remain reproducible:

1. `domain_contract_loader.py` can load `contract.yaml`
2. `session_start.py` can inject kernel-driver context and report validator preflight success
3. `pre_task_check.py` can activate `kernel-driver` rules with `ok: true`
4. `post_task_check.py` can emit advisory findings for violating fixtures
5. `post_task_check.py` can stay clean for compliant fixtures

## Current Domain Validators

### `irql_safety_validator.py`

Purpose:

- detect IRQL-sensitive API usage in dispatch-level or equivalent high-IRQL code paths

Current advisory findings:

- `KD-IRQL-001`

### `pool_type_validator.py`

Purpose:

- detect legacy pool allocation guidance that does not make pool intent explicit

Current advisory findings:

- `KD-POOL-001`

## Reviewer Expectations

Reviewer-consumable output should preserve these properties:

- built-in kernel-driver evidence checks remain visible
- domain-validator findings are surfaced as advisory warnings
- compliant baselines still exercise the same path without producing false positives
- validation output stays understandable without reading the validator source first

## Out of Scope Today

The following are not yet required for this repo to be considered healthy:

- hard-stop enforcement for domain validators
- real WDK build integration
- real Driver Verifier output ingestion
- SDV result ingestion from a connected driver repo
- fully automated discovery of a separate driver repository

## Next Validation Milestone

The next meaningful milestone is to connect a real driver repository and verify that:

- the first confirmed driver facts can be captured
- the existing advisory validators still produce sensible results on real evidence
- the current payload shape is general enough for a second round of driver-specific checks
