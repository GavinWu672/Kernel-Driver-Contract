#!/usr/bin/env python3
"""
Advisory validator for IRP dispatch routine registration completeness.

Rules enforced:
  KD-009  dispatch-routine-registered

Checks:
  1. Any IRP_MJ_* constant referenced in the code (as a handler target or
     comment) should have a corresponding MajorFunction assignment in
     DriverEntry / the same snippet.
  2. Handlers assigned to MajorFunction must be actual function names, not
     NULL or a stub placeholder.
  3. If DriverEntry is present but no MajorFunction assignments are found,
     flag as a gap (advisory).

Limitations:
  - Text-based analysis only; cannot resolve macro-expanded handler tables.
  - Cross-file handler references are not followed.
"""

import re

from governance_tools.validator_interface import DomainValidator, ValidatorResult

# All standard IRP major function codes
_ALL_IRP_MJ = [
    "IRP_MJ_CREATE",
    "IRP_MJ_CREATE_NAMED_PIPE",
    "IRP_MJ_CLOSE",
    "IRP_MJ_READ",
    "IRP_MJ_WRITE",
    "IRP_MJ_QUERY_INFORMATION",
    "IRP_MJ_SET_INFORMATION",
    "IRP_MJ_QUERY_EA",
    "IRP_MJ_SET_EA",
    "IRP_MJ_FLUSH_BUFFERS",
    "IRP_MJ_QUERY_VOLUME_INFORMATION",
    "IRP_MJ_SET_VOLUME_INFORMATION",
    "IRP_MJ_DIRECTORY_CONTROL",
    "IRP_MJ_FILE_SYSTEM_CONTROL",
    "IRP_MJ_DEVICE_CONTROL",
    "IRP_MJ_INTERNAL_DEVICE_CONTROL",
    "IRP_MJ_SHUTDOWN",
    "IRP_MJ_LOCK_CONTROL",
    "IRP_MJ_CLEANUP",
    "IRP_MJ_CREATE_MAILSLOT",
    "IRP_MJ_QUERY_SECURITY",
    "IRP_MJ_SET_SECURITY",
    "IRP_MJ_POWER",
    "IRP_MJ_SYSTEM_CONTROL",
    "IRP_MJ_DEVICE_CHANGE",
    "IRP_MJ_QUERY_QUOTA",
    "IRP_MJ_SET_QUOTA",
    "IRP_MJ_PNP",
]

# Pattern: DriverObject->MajorFunction[IRP_MJ_*] = <something>;
_ASSIGNMENT_RE = re.compile(
    r"DriverObject\s*->\s*MajorFunction\s*\[\s*(IRP_MJ_\w+)\s*\]\s*=\s*([^;]+);",
    re.MULTILINE,
)

# Pattern: DriverEntry function signature present
_DRIVER_ENTRY_RE = re.compile(r"\bDriverEntry\s*\(", re.IGNORECASE)

# NULL assignments are suspicious
_NULL_HANDLER_RE = re.compile(r"\bNULL\b", re.IGNORECASE)


class DispatchRoutineValidator(DomainValidator):

    @property
    def rule_ids(self) -> list[str]:
        return ["kernel-driver", "KD-009"]

    def validate(self, payload: dict) -> ValidatorResult:
        checks = payload.get("checks", {})
        code = (
            checks.get("driver_code")
            or checks.get("diff_text")
            or payload.get("driver_code")
            or ""
        )

        warnings: list[str] = []

        # Collect all MajorFunction assignments
        assignments: dict[str, str] = {}
        for m in _ASSIGNMENT_RE.finditer(code):
            irp_code = m.group(1).strip()
            handler = m.group(2).strip()
            assignments[irp_code] = handler

        # Flag NULL handler assignments
        for irp_code, handler in assignments.items():
            if _NULL_HANDLER_RE.search(handler):
                warnings.append(
                    f"KD-DISP-001: MajorFunction[{irp_code}] is assigned NULL; "
                    "unhandled IRPs should use a passthrough stub, not NULL"
                )

        # If DriverEntry is present but no assignments found, flag as gap
        has_driver_entry = bool(_DRIVER_ENTRY_RE.search(code))
        if has_driver_entry and not assignments:
            warnings.append(
                "KD-DISP-002: DriverEntry detected but no "
                "DriverObject->MajorFunction[...] assignments found in snippet; "
                "verify handler registration is complete"
            )

        # Flag IRP_MJ_* codes referenced in code but without an assignment
        referenced = set()
        for irp in _ALL_IRP_MJ:
            if re.search(rf"\b{re.escape(irp)}\b", code):
                referenced.add(irp)
        unregistered = referenced - set(assignments.keys())
        for irp in sorted(unregistered):
            # Only warn if there are some assignments present (otherwise covered by DISP-002)
            if assignments:
                warnings.append(
                    f"KD-DISP-003: '{irp}' referenced in code but not assigned "
                    "in DriverObject->MajorFunction; verify intent"
                )

        return ValidatorResult(
            ok=True,  # advisory — never hard-stops on its own
            rule_ids=self.rule_ids,
            violations=[],
            warnings=warnings,
            evidence_summary=(
                f"MajorFunction assignments found: {len(assignments)}; "
                f"IRP codes referenced: {len(referenced)}"
            ),
            metadata={"mode": "advisory"},
        )
