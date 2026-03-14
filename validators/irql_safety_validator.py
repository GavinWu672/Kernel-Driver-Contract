#!/usr/bin/env python3
"""
Advisory validator for IRQL-sensitive kernel-driver patterns.
"""

from governance_tools.validator_interface import DomainValidator, ValidatorResult


class IrqlSafetyValidator(DomainValidator):
    PAGED_APIS_FORBIDDEN_AT_DISPATCH = [
        "ExAllocatePoolWithTag",
        "ZwCreateFile",
        "ZwQueryInformationFile",
        "KeWaitForSingleObject",
        "IoCreateDevice",
    ]

    @property
    def rule_ids(self) -> list[str]:
        return ["kernel-driver", "KD-002", "KD-003"]

    def validate(self, payload: dict) -> ValidatorResult:
        checks = payload.get("checks", {})
        dispatch_code = (
            payload.get("dispatch_level_code")
            or checks.get("dispatch_level_code")
            or checks.get("driver_code")
            or checks.get("diff_text")
            or ""
        )
        violations = [
            f"KD-IRQL-001: '{api}' called at DISPATCH_LEVEL or above"
            for api in self.PAGED_APIS_FORBIDDEN_AT_DISPATCH
            if api in dispatch_code
        ]
        return ValidatorResult(
            ok=len(violations) == 0,
            rule_ids=self.rule_ids,
            violations=violations,
            evidence_summary=f"Checked {len(self.PAGED_APIS_FORBIDDEN_AT_DISPATCH)} IRQL-sensitive APIs",
            metadata={"mode": "advisory"},
        )
