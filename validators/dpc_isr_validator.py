#!/usr/bin/env python3
"""
Hard-stop validator for DPC and ISR routine safety.

Rules enforced:
  KD-007  dpc-isr-nonblocking

DPC routines (KDEFERRED_ROUTINE) run at DISPATCH_LEVEL.
ISR routines (KSERVICE_ROUTINE) run at DIRQL (above DISPATCH_LEVEL).
Neither may call blocking, pageable, or wait-based kernel APIs.

Detection strategy:
  1. Identify DPC/ISR routine signatures in the code snippet.
  2. If found, scan the same snippet for forbidden APIs.
  3. Even without a signature, if the payload key is 'dpc_code' or 'isr_code',
     apply the same forbidden-API check unconditionally.
"""

import re

from governance_tools.validator_interface import DomainValidator, ValidatorResult

# Signatures that indicate DPC or ISR context
_DPC_ISR_SIGNATURES = [
    re.compile(r"\bKDEFERRED_ROUTINE\b"),
    re.compile(r"\bKSERVICE_ROUTINE\b"),
    re.compile(r"\bIO_DPC_ROUTINE\b"),
    re.compile(r"\bKeInitializeDpc\b"),
    re.compile(r"\bIoInitializeDpcRequest\b"),
    re.compile(r"\bIoRequestDpc\b"),
    re.compile(r"\bKeInsertQueueDpc\b"),
]

# APIs forbidden inside DPC/ISR (blocking, pageable, or wait-based)
_FORBIDDEN_IN_DPC_ISR = [
    # Synchronous waits
    "KeWaitForSingleObject",
    "KeWaitForMultipleObjects",
    "KeWaitForMutexObject",
    "KeDelayExecutionThread",
    # Paged pool allocators
    "ExAllocatePool",
    "ExAllocatePoolWithTag",
    # Fast/push-lock (APC_LEVEL only)
    "ExAcquireFastMutex",
    "ExAcquireFastMutexUnsafe",
    "ExAcquirePushLockExclusive",
    "ExAcquirePushLockShared",
    # File / registry I/O (blocks until completion)
    "ZwCreateFile",
    "ZwOpenFile",
    "ZwReadFile",
    "ZwWriteFile",
    "ZwQueryInformationFile",
    "ZwOpenKey",
    "ZwQueryValueKey",
    # Device creation (touches paged memory)
    "IoCreateDevice",
    "IoCreateSymbolicLink",
    # Thread creation / termination
    "PsCreateSystemThread",
    "PsTerminateSystemThread",
]


def _has_dpc_isr_signature(code: str) -> bool:
    return any(sig.search(code) for sig in _DPC_ISR_SIGNATURES)


class DpcIsrValidator(DomainValidator):

    @property
    def rule_ids(self) -> list[str]:
        return ["kernel-driver", "KD-007"]

    def validate(self, payload: dict) -> ValidatorResult:
        checks = payload.get("checks", {})

        # Explicit DPC/ISR payload keys take priority
        explicit_dpc_isr = (
            "dpc_code" in payload
            or "isr_code" in payload
            or "dpc_code" in checks
            or "isr_code" in checks
        )

        code = (
            payload.get("dpc_code")
            or payload.get("isr_code")
            or checks.get("dpc_code")
            or checks.get("isr_code")
            or checks.get("driver_code")
            or checks.get("diff_text")
            or ""
        )

        has_signature = _has_dpc_isr_signature(code)
        in_dpc_isr_context = explicit_dpc_isr or has_signature

        if not in_dpc_isr_context:
            return ValidatorResult(
                ok=True,
                rule_ids=self.rule_ids,
                violations=[],
                evidence_summary="No DPC/ISR signatures detected; skipped",
                metadata={"mode": "advisory", "skipped": True},
            )

        violations: list[str] = []
        for api in _FORBIDDEN_IN_DPC_ISR:
            if re.search(rf"\b{re.escape(api)}\b", code):
                violations.append(
                    f"KD-DPC-001: '{api}' is forbidden inside a DPC/ISR routine "
                    f"(runs at DISPATCH_LEVEL or higher)"
                )

        return ValidatorResult(
            ok=len(violations) == 0,
            rule_ids=self.rule_ids,
            violations=violations,
            evidence_summary=(
                f"Checked {len(_FORBIDDEN_IN_DPC_ISR)} forbidden DPC/ISR APIs; "
                f"signature={'found' if has_signature else 'explicit-key'}"
            ),
            metadata={"mode": "hard-stop"},
        )
