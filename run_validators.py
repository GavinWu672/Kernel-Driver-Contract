#!/usr/bin/env python3
"""
CI/CD pipeline runner for kernel-driver contract validators.

Usage:
  # Run all validators against a single JSON payload file:
  python run_validators.py fixture.checks.json

  # Run against all fixtures in a directory:
  python run_validators.py fixtures/

  # Run against all *.checks.json files under the project root:
  python run_validators.py

  # Run a single named validator only:
  python run_validators.py --validator irql fixtures/irql_violation.checks.json

Exit codes:
  0  All hard-stop validators passed (warnings allowed)
  1  One or more hard-stop violations detected
  2  Usage / file-not-found error

Output format:
  Plain-text summary per fixture + machine-readable JSON summary to stdout
  when --json flag is provided.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

# ── Validator discovery ──────────────────────────────────────────────────────

VALIDATORS_DIR = Path(__file__).parent / "validators"

# Map short names to module file names (order controls execution sequence)
_VALIDATOR_MODULES: list[str] = [
    "irql_safety_validator",
    "pool_type_validator",
    "sync_primitive_validator",
    "dpc_isr_validator",
    "pageable_section_validator",
    "dispatch_routine_validator",
    "static_analysis_validator",
]

# Hard-stop rule IDs (copied from contract.yaml; runner enforces exit code 1)
_HARD_STOP_RULES: set[str] = {
    "KD-002",
    "KD-003",
    "KD-006",
    "KD-007",
    "KD-010",
}


# ── Stub interface (used when governance_tools is not installed) ─────────────

class _ValidatorResult:
    def __init__(
        self,
        ok: bool,
        rule_ids: list[str],
        violations: list[str] | None = None,
        warnings: list[str] | None = None,
        evidence_summary: str = "",
        metadata: dict | None = None,
    ) -> None:
        self.ok = ok
        self.rule_ids = rule_ids
        self.violations = violations or []
        self.warnings = warnings or []
        self.evidence_summary = evidence_summary
        self.metadata = metadata or {}


class _DomainValidator:
    @property
    def rule_ids(self) -> list[str]:
        return []

    def validate(self, payload: dict) -> _ValidatorResult:  # pragma: no cover
        raise NotImplementedError


def _inject_stubs() -> None:
    """Inject minimal governance_tools stubs so validators import cleanly."""
    import types

    pkg = types.ModuleType("governance_tools")
    iface = types.ModuleType("governance_tools.validator_interface")
    iface.DomainValidator = _DomainValidator        # type: ignore[attr-defined]
    iface.ValidatorResult = _ValidatorResult        # type: ignore[attr-defined]
    sys.modules["governance_tools"] = pkg
    sys.modules["governance_tools.validator_interface"] = iface


# ── Loader ───────────────────────────────────────────────────────────────────

def _load_validator(module_name: str) -> _DomainValidator | None:
    path = VALIDATORS_DIR / f"{module_name}.py"
    if not path.exists():
        print(f"  [WARN] validator not found: {path}", file=sys.stderr)
        return None
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)          # type: ignore[arg-type]
    spec.loader.exec_module(mod)                         # type: ignore[union-attr]
    # Find the first DomainValidator subclass defined in the module
    for attr in dir(mod):
        obj = getattr(mod, attr)
        try:
            if (
                isinstance(obj, type)
                and issubclass(obj, _DomainValidator)
                and obj is not _DomainValidator
            ):
                return obj()
        except TypeError:
            continue
    print(f"  [WARN] No DomainValidator subclass in {path}", file=sys.stderr)
    return None


# ── Runner ───────────────────────────────────────────────────────────────────

def _run_fixture(
    fixture_path: Path,
    validators: list[tuple[str, _DomainValidator]],
) -> dict[str, Any]:
    """Run all validators against one fixture file. Returns a result dict."""
    try:
        raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"fixture": str(fixture_path), "error": str(exc), "passed": False}

    # Normalise: wrap top-level as payload with a 'checks' key if needed
    payload: dict[str, Any]
    if "checks" in raw:
        payload = raw
    else:
        payload = {"checks": raw, **raw}

    results: list[dict] = []
    hard_stop_hit = False

    for name, validator in validators:
        try:
            result = validator.validate(payload)
        except Exception as exc:
            results.append({"validator": name, "error": str(exc), "ok": False})
            continue

        is_hard_stop = bool(
            set(result.rule_ids) & _HARD_STOP_RULES
            and not result.ok
        )
        if is_hard_stop:
            hard_stop_hit = True

        results.append({
            "validator": name,
            "ok": result.ok,
            "hard_stop": is_hard_stop,
            "violations": result.violations,
            "warnings": result.warnings,
            "evidence_summary": result.evidence_summary,
            "metadata": result.metadata,
        })

    return {
        "fixture": str(fixture_path),
        "passed": not hard_stop_hit,
        "results": results,
    }


def _collect_fixtures(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.glob("*.checks.json"))
    # Default: project root
    return sorted(Path(__file__).parent.glob("fixtures/**/*.checks.json"))


def _print_report(fixture_result: dict[str, Any], verbose: bool) -> None:
    fixture = fixture_result.get("fixture", "?")
    passed = fixture_result.get("passed", False)
    status = "PASS" if passed else "FAIL"
    print(f"\n{'='*60}")
    print(f"  {status}  {fixture}")
    print(f"{'='*60}")

    if "error" in fixture_result:
        print(f"  ERROR: {fixture_result['error']}")
        return

    for r in fixture_result.get("results", []):
        if r.get("error"):
            print(f"  [{r['validator']}] ERROR: {r['error']}")
            continue

        ok = r.get("ok", True)
        hs = r.get("hard_stop", False)
        tag = "HARD-STOP" if hs else ("WARN" if not ok else "ok")
        summary = r.get("evidence_summary", "")
        print(f"  [{r['validator']:40s}] {tag:9s}  {summary}")

        if verbose or not ok:
            for v in r.get("violations", []):
                print(f"      VIOLATION: {v}")
            for w in r.get("warnings", []):
                print(f"      warning  : {w}")


# ── Entry point ──────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Kernel-driver contract validator runner"
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to a .checks.json file, a directory, or omit for all fixtures",
    )
    parser.add_argument(
        "--validator", "-V",
        help="Run only this validator (module name without .py)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Print machine-readable JSON summary to stdout after text output",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print warnings even for passing validators",
    )
    args = parser.parse_args(argv)

    # Inject stubs before importing validators
    _inject_stubs()

    # Determine which validators to run
    module_names = (
        [args.validator] if args.validator else _VALIDATOR_MODULES
    )
    validators: list[tuple[str, _DomainValidator]] = []
    for name in module_names:
        v = _load_validator(name)
        if v:
            validators.append((name, v))

    if not validators:
        print("ERROR: No validators loaded.", file=sys.stderr)
        return 2

    # Collect fixture files
    target = Path(args.target) if args.target else Path(__file__).parent
    fixtures = _collect_fixtures(target)

    if not fixtures:
        print(f"ERROR: No *.checks.json files found at {target}", file=sys.stderr)
        return 2

    all_results: list[dict] = []
    overall_pass = True

    for fixture_path in fixtures:
        fr = _run_fixture(fixture_path, validators)
        all_results.append(fr)
        _print_report(fr, verbose=args.verbose)
        if not fr.get("passed", False):
            overall_pass = False

    # Summary line
    total = len(all_results)
    passed = sum(1 for r in all_results if r.get("passed"))
    print(f"\n{'='*60}")
    print(f"  SUMMARY: {passed}/{total} fixtures passed")
    if overall_pass:
        print("  RESULT : ALL HARD-STOP CHECKS PASSED")
    else:
        print("  RESULT : HARD-STOP VIOLATIONS DETECTED — blocking merge")
    print(f"{'='*60}\n")

    if args.json:
        print(json.dumps({"overall_pass": overall_pass, "fixtures": all_results}, indent=2))

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
