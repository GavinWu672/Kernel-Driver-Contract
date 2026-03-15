#!/usr/bin/env python3
"""
Kernel-driver source scanner.

Scans real *.c / *.h driver source files, classifies each function by its
IRQL context, and emits .checks.json payloads that run_validators.py can
consume directly.

Usage:
  # Scan a directory — one checks.json per .c file written to ./scan_output/
  python scan_source.py path/to/driver/

  # Scan a single file
  python scan_source.py path/to/driver/file.c

  # Write output to a custom directory
  python scan_source.py path/to/driver/ --output-dir my_results/

  # Aggregate all files into one checks.json per directory
  python scan_source.py path/to/driver/ --aggregate

  # Scan + immediately run validators (no JSON files written)
  python scan_source.py path/to/driver/ --run

Output format per file (same shape as hand-written fixture files):
  {
    "source_file": "<path>",
    "driver_code":          "<full file text>",
    "dispatch_level_code":  "<dispatch-level functions concatenated>",
    "dpc_code":             "<DPC routine functions concatenated>",
    "isr_code":             "<ISR routine functions concatenated>",
    "pageable_functions":   ["FuncA", "FuncB"],
    "dispatch_handlers":    {"IRP_MJ_CREATE": "DriverCreate", ...},
    "changed_files":        ["<path>"],
    "diagnostics":          [],
    "summary":              {"failed": 0},
    "warnings":             [],
    "errors":               []
  }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

# ── Regex patterns ────────────────────────────────────────────────────────────

# WDM DPC / ISR type annotations (in function signature or preceding line)
# KMDF equivalents: EVT_WDF_INTERRUPT_DPC, EVT_WDF_TIMER_FUNC, EVT_WDF_DPC_FUNC
_DPC_SIGNATURE = re.compile(
    r"\b(KDEFERRED_ROUTINE|IO_DPC_ROUTINE|DPC_ROUTINE"
    r"|EVT_WDF_INTERRUPT_DPC|EVT_WDF_TIMER_FUNC|EVT_WDF_DPC_FUNC)\b"
)
# WDM ISR / KMDF ISR equivalents
_ISR_SIGNATURE = re.compile(
    r"\b(KSERVICE_ROUTINE|KMESSAGE_SERVICE_ROUTINE|EVT_WDF_INTERRUPT_ISR)\b"
)

# pageable section marker: #pragma alloc_text(PAGE, FuncName)
_ALLOC_TEXT_PAGE = re.compile(
    r"#\s*pragma\s+alloc_text\s*\(\s*PAGE\s*,\s*(\w+)\s*\)", re.IGNORECASE
)

# WDM dispatch routine registration: DriverObject->MajorFunction[IRP_MJ_*] = Name;
_MAJOR_FUNC_RE = re.compile(
    r"DriverObject\s*->\s*MajorFunction\s*\[\s*(IRP_MJ_\w+)\s*\]\s*=\s*(\w+)\s*;",
    re.MULTILINE,
)

# WDM DPC registration: KeInitializeDpc / IoInitializeDpcRequest
# KMDF DPC registration:
#   WDF_DPC_CONFIG_INIT(&cfg, DpcFunc)          — 2nd arg is callback
#   WDF_TIMER_CONFIG_INIT(&cfg, TimerFunc)       — 2nd arg is callback
#   WDF_INTERRUPT_CONFIG_INIT(&cfg, IsrFunc, DpcFunc) — 3rd arg is DPC callback
_DPC_REGISTRATION = re.compile(
    r"(?:"
    # WDM
    r"(?:KeInitializeDpc|IoInitializeDpcRequest|KeInsertQueueDpc)\s*\([^,)]*,\s*(\w+)"
    r"|"
    # KMDF DPC / timer config init — function name is 2nd arg
    r"(?:WDF_DPC_CONFIG_INIT|WDF_TIMER_CONFIG_INIT)\s*\([^,)]+,\s*(\w+)"
    r"|"
    # KMDF interrupt config init — DPC is 3rd arg
    r"WDF_INTERRUPT_CONFIG_INIT\s*\([^,)]+,[^,)]+,\s*(\w+)"
    r")",
    re.MULTILINE,
)

# WDM ISR registration: IoConnectInterrupt — ServiceRoutine is 3rd arg
# KMDF ISR registration: WDF_INTERRUPT_CONFIG_INIT(&cfg, IsrFunc, DpcFunc)
#                         — ISR is 2nd arg
_ISR_REGISTRATION = re.compile(
    r"(?:"
    # WDM
    r"IoConnectInterrupt\s*\([^,)]+,[^,)]+,\s*(\w+)"
    r"|"
    # KMDF interrupt config init — ISR is 2nd arg
    r"WDF_INTERRUPT_CONFIG_INIT\s*\([^,)]+,\s*(\w+)"
    r")",
    re.MULTILINE,
)

# Spinlock usage — heuristic for DISPATCH_LEVEL context inside a function
# Covers both WDM (KeAcquireSpinLock) and KMDF (WdfSpinLockAcquire, WdfInterruptAcquireLock)
_SPINLOCK_USE = re.compile(
    r"\bKeAcquireSpinLock\b"
    r"|\bKeAcquireSpinLockAtDpcLevel\b"
    r"|\bWdfSpinLockAcquire\b"
    r"|\bWdfInterruptAcquireLock\b"
)

# Raise IRQL to DISPATCH (WDM)
_RAISE_IRQL = re.compile(r"\bKeRaiseIrql\s*\(\s*DISPATCH_LEVEL")

# ── KMDF EVT_WDF forward-declaration registry ─────────────────────────────────
# Pattern: EVT_WDF_<TYPE>  FuncName;
# Captures (evt_type, func_name)
_WDF_FORWARD_DECL = re.compile(
    r"\bEVT_WDF_(\w+)\s+(\w+)\s*;", re.MULTILINE
)

# Maps EVT_WDF_<suffix> → IRQL context
# DISPATCH_LEVEL callbacks
_WDF_DPC_TYPES = {
    "INTERRUPT_DPC",
    "TIMER_FUNC",
    "TIMER",          # older alias
    "DPC_FUNC",
    "PROGRAM_DMA",
    "INTERRUPT_WORKITEM",   # also runs at PASSIVE but involves DPC handoff; treat as dpc
}
# DIRQL (above DISPATCH_LEVEL).
# NOTE: 'isr' here means "interrupt-related callback family" for policy
# classification purposes, not narrowly the ISR entry point.
# INTERRUPT_ENABLE/DISABLE are called with interrupts disabled at DIRQL
# (same execution context as INTERRUPT_ISR), so they belong in this family.
_WDF_ISR_TYPES = {
    "INTERRUPT_ISR",
    "INTERRUPT_SYNCHRONIZE",
    "INTERRUPT_ENABLE",
    "INTERRUPT_DISABLE",
}


def _build_wdf_registry(sources: list[Path]) -> dict[str, str]:
    """
    Scan all source files for EVT_WDF_<TYPE> FuncName; forward declarations
    and return a mapping {func_name: label}.
    label is one of 'dpc', 'isr', or 'other'.

    Design principle: every EVT_WDF_* forward declaration is written into the
    registry so that _classify_func can use framework registration as
    authoritative truth and never fall through to the spinlock heuristic for
    a known WDF callback.  Unknown/passive callback types (IO queue, PnP,
    power, work items, etc.) receive label 'other'.
    """
    registry: dict[str, str] = {}
    for path in sources:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _WDF_FORWARD_DECL.finditer(text):
            evt_type = m.group(1).upper()
            func_name = m.group(2)
            if evt_type in _WDF_ISR_TYPES:
                registry[func_name] = "isr"
            elif evt_type in _WDF_DPC_TYPES:
                registry[func_name] = "dpc"
            else:
                # All other EVT_WDF_* types (IO queue, PnP, power, work items,
                # completion routines, etc.) run at PASSIVE_LEVEL or at an
                # IRQL determined by queue config — outside isr/dpc scope.
                # Register as 'other' so the spinlock heuristic cannot
                # override this known framework callback.
                registry[func_name] = "other"
    return registry

# Broad function definition pattern (C-style, not C++)
# Matches:   ReturnType [__stdcall] FuncName(args...) [comment] {
# Handles WDK pattern where /*++...--*/ comment sits between ')' and '{'.
_FUNC_DEF_RE = re.compile(
    r"""
    ^                               # start of line
    (?:[\w\s\*]+?)                  # return type (non-greedy, may span lines)
    \b(\w+)\s*                      # function name (captured)
    \(                              # opening paren
    [^)]*                           # params (no nested parens needed)
    \)                              # closing paren
    \s*                             # optional whitespace / newlines
    (?:/\*[\s\S]*?\*/\s*)*          # skip 0..n block comments (WDK /*++--*/ style)
    (?://[^\n]*\n\s*)*              # skip 0..n line comments
    \{                              # opening brace — function body starts
    """,
    re.VERBOSE | re.MULTILINE,
)

# C control-flow keywords and other non-function identifiers to exclude
_C_KEYWORDS = frozenset({
    "if", "else", "while", "for", "switch", "do", "return", "sizeof",
    "typeof", "alignof", "case", "default", "break", "continue", "goto",
    "typedef", "struct", "union", "enum", "extern", "static", "inline",
    "__if_exists", "__if_not_exists", "__assume",
})


# ── Function extractor ───────────────────────────────────────────────────────

class FuncInfo(NamedTuple):
    name: str
    body: str          # full text from opening '{' to matching '}'
    start: int         # character offset in file


def extract_functions(code: str) -> list[FuncInfo]:
    """
    Extract top-level function definitions from C source text.
    Uses brace-counting; handles nested braces but not preprocessor tricks.
    """
    functions: list[FuncInfo] = []
    for m in _FUNC_DEF_RE.finditer(code):
        name = m.group(1)
        # Skip C control-flow keywords and other non-function identifiers
        if name in _C_KEYWORDS:
            continue
        brace_start = m.end() - 1  # position of '{'
        depth = 0
        end = brace_start
        for i, ch in enumerate(code[brace_start:], brace_start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        body = code[brace_start:end]
        functions.append(FuncInfo(name=name, body=body, start=m.start()))
    return functions


# ── IRQL classifier ──────────────────────────────────────────────────────────

class FileAnalysis(NamedTuple):
    path: Path
    full_text: str
    pageable_funcs: set[str]
    dispatch_handlers: dict[str, str]   # IRP_MJ_* → handler name
    dpc_registered: set[str]            # names registered as DPC callbacks
    isr_registered: set[str]            # names registered as ISR callbacks
    wdf_registry: dict[str, str]        # EVT_WDF forward-decl map: name → context
    functions: list[FuncInfo]


def _extract_registered_names(pattern: re.Pattern, text: str) -> set[str]:
    """
    Extract function names from a registration pattern that may have multiple
    capture groups (one per alternative branch).  Returns non-empty matches.
    """
    names: set[str] = set()
    for m in pattern.finditer(text):
        for g in m.groups():
            if g:
                names.add(g)
    return names


def _analyse_file(path: Path, wdf_registry: dict[str, str] | None = None) -> FileAnalysis:
    text = path.read_text(encoding="utf-8", errors="replace")

    pageable = set(_ALLOC_TEXT_PAGE.findall(text))
    handlers = {m.group(1): m.group(2) for m in _MAJOR_FUNC_RE.finditer(text)}
    dpc_reg = _extract_registered_names(_DPC_REGISTRATION, text)
    isr_reg = _extract_registered_names(_ISR_REGISTRATION, text)
    funcs = extract_functions(text)

    return FileAnalysis(
        path=path,
        full_text=text,
        pageable_funcs=pageable,
        dispatch_handlers=handlers,
        dpc_registered=dpc_reg,
        isr_registered=isr_reg,
        wdf_registry=wdf_registry or {},
        functions=funcs,
    )


def _classify_func(func: FuncInfo, analysis: FileAnalysis) -> str:
    """
    Returns the IRQL context key for this function:
      'dpc'      - DPC routine (runs at DISPATCH_LEVEL via framework callback)
      'isr'      - ISR routine (runs at DIRQL)
      'dispatch' - runs at DISPATCH_LEVEL (spinlock-held or KeRaiseIrql evidence)
      'other'    - all other code: helpers, init paths, pageable routines, unknown
                   (previously named 'driver'; renamed to avoid false semantic clarity)
    """
    name = func.name
    body = func.body

    # Look at the ~200 chars before the opening brace for type annotations
    pre = analysis.full_text[max(0, func.start - 200): func.start]

    if _DPC_SIGNATURE.search(pre) or name in analysis.dpc_registered:
        return "dpc"
    if _ISR_SIGNATURE.search(pre) or name in analysis.isr_registered:
        return "isr"
    # KMDF EVT_WDF forward-declaration lookup (cross-file registry)
    if name in analysis.wdf_registry:
        return analysis.wdf_registry[name]
    if _SPINLOCK_USE.search(body) or _RAISE_IRQL.search(body):
        return "dispatch"
    return "other"


# ── Payload builder ──────────────────────────────────────────────────────────

def build_payload(analysis: FileAnalysis) -> dict:
    buckets: dict[str, list[str]] = {
        "dpc": [],
        "isr": [],
        "dispatch": [],
        "other": [],
    }
    # classified_functions: label → list of function names (for precision tooling)
    classified_functions: dict[str, list[str]] = {
        "dpc": [], "isr": [], "dispatch": [], "other": []
    }

    for func in analysis.functions:
        key = _classify_func(func, analysis)
        buckets[key].append(func.body)
        classified_functions[key].append(func.name)

    def join(parts: list[str]) -> str:
        return "\n\n".join(parts)

    payload: dict = {
        "source_file": str(analysis.path),
        "driver_code": analysis.full_text,
        "changed_files": [str(analysis.path)],
        "pageable_functions": sorted(analysis.pageable_funcs),
        "dispatch_handlers": analysis.dispatch_handlers,
        "classified_functions": classified_functions,
        "diagnostics": [],
        "summary": {"failed": 0},
        "warnings": [],
        "errors": [],
    }

    if buckets["dispatch"]:
        payload["dispatch_level_code"] = join(buckets["dispatch"])
    if buckets["dpc"]:
        payload["dpc_code"] = join(buckets["dpc"])
    if buckets["isr"]:
        payload["isr_code"] = join(buckets["isr"])
    if buckets["other"]:
        payload["other_functions_code"] = join(buckets["other"])

    return payload


# ── Aggregate builder ─────────────────────────────────────────────────────────

def aggregate_payloads(payloads: list[dict], source_dir: Path) -> dict:
    """Merge all per-file payloads into one directory-level payload."""

    def merge_key(key: str) -> str:
        parts = [p[key] for p in payloads if key in p and p[key]]
        return "\n\n/* --- next file --- */\n\n".join(parts)

    all_files = [f for p in payloads for f in p.get("changed_files", [])]
    all_pageable = sorted({f for p in payloads for f in p.get("pageable_functions", [])})
    all_handlers: dict = {}
    for p in payloads:
        all_handlers.update(p.get("dispatch_handlers", {}))

    agg: dict = {
        "source_dir": str(source_dir),
        "driver_code": merge_key("driver_code"),
        "changed_files": all_files,
        "pageable_functions": all_pageable,
        "dispatch_handlers": all_handlers,
        "diagnostics": [],
        "summary": {"failed": 0},
        "warnings": [],
        "errors": [],
    }

    for key in ("dispatch_level_code", "dpc_code", "isr_code"):
        merged = merge_key(key)
        if merged:
            agg[key] = merged

    return agg


# ── File collection ──────────────────────────────────────────────────────────

def collect_sources(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    sources = sorted(
        list(target.rglob("*.c")) + list(target.rglob("*.h"))
    )
    # Skip generated / build output files
    skip_patterns = {"obj", "objfre", "objchk", "build", ".vs", "__pycache__"}
    return [
        p for p in sources
        if not any(part.lower() in skip_patterns for part in p.parts)
    ]


# ── Reporting helper ─────────────────────────────────────────────────────────

def _print_file_summary(payload: dict) -> None:
    src = payload.get("source_file") or payload.get("source_dir", "?")
    cf = payload.get("classified_functions", {})
    funcs_disp = len(cf.get("dispatch", []))
    funcs_dpc  = len(cf.get("dpc", []))
    funcs_isr  = len(cf.get("isr", []))
    funcs_other = len(cf.get("other", []))
    handlers   = len(payload.get("dispatch_handlers", {}))
    pageable   = len(payload.get("pageable_functions", []))
    print(
        f"  {Path(src).name:<40s} "
        f"isr={funcs_isr} dpc={funcs_dpc} dispatch={funcs_disp} "
        f"other={funcs_other} handlers={handlers} pageable={pageable}"
    )


# ── Entry point ──────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan kernel-driver C sources and emit validator payloads"
    )
    parser.add_argument("target", help="Source file or directory to scan")
    parser.add_argument(
        "--output-dir", "-o",
        default="scan_output",
        help="Directory to write .checks.json files (default: scan_output/)",
    )
    parser.add_argument(
        "--aggregate", "-a",
        action="store_true",
        help="Merge all files into one checks.json per directory",
    )
    parser.add_argument(
        "--run", "-r",
        action="store_true",
        help="Run run_validators.py on the output immediately after scanning",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
    )
    args = parser.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        print(f"ERROR: {target} does not exist", file=sys.stderr)
        return 2

    sources = collect_sources(target)
    if not sources:
        print(f"ERROR: no .c/.h files found under {target}", file=sys.stderr)
        return 2

    print(f"Scanning {len(sources)} source file(s) from {target}\n")

    # Build WDF callback registry from all files before per-file analysis.
    # This resolves cross-file EVT_WDF_* forward declarations (KMDF pattern).
    wdf_registry = _build_wdf_registry(sources)
    if wdf_registry:
        print(f"WDF callback registry: {len(wdf_registry)} entries detected\n")

    payloads: list[dict] = []
    for src in sources:
        try:
            analysis = _analyse_file(src, wdf_registry)
            payload = build_payload(analysis)
            payloads.append(payload)
            if args.verbose:
                _print_file_summary(payload)
        except Exception as exc:
            print(f"  [WARN] failed to parse {src}: {exc}", file=sys.stderr)

    if not payloads:
        print("ERROR: no payloads built", file=sys.stderr)
        return 2

    # Print summary table even without --verbose
    if not args.verbose:
        for p in payloads:
            _print_file_summary(p)

    # Write output
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    if args.aggregate:
        agg = aggregate_payloads(payloads, target if target.is_dir() else target.parent)
        out_path = out_dir / (target.stem + "_aggregate.checks.json")
        out_path.write_text(json.dumps(agg, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(out_path)
        print(f"\nAggregate output → {out_path}")
    else:
        for payload in payloads:
            stem = Path(payload["source_file"]).stem
            out_path = out_dir / f"{stem}.checks.json"
            # If multiple files share the same stem, disambiguate
            counter = 1
            while out_path in written:
                out_path = out_dir / f"{stem}_{counter}.checks.json"
                counter += 1
            out_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            written.append(out_path)
        print(f"\n{len(written)} checks.json file(s) written to {out_dir}/")

    # Optionally run validators
    if args.run:
        import subprocess
        runner = Path(__file__).parent / "run_validators.py"
        cmd = [sys.executable, str(runner), str(out_dir)]
        print(f"\nRunning: {' '.join(cmd)}\n")
        result = subprocess.run(cmd)
        return result.returncode

    print(f"\nNext step: python run_validators.py {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
