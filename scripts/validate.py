#!/usr/bin/env python3
"""Validates community-submitted benchmark reports under results/.

Reports come from https://github.com/skywalk1411/lemonade_lab (bench/report.py's
build_json_report output), but this validator only depends on the JSON shape,
not on that project's code, so other tools could submit compatible reports too.

Usage:
    python scripts/validate.py                  # validate every file in results/
    python scripts/validate.py results/foo.json  # validate specific files
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"

KNOWN_WORKLOADS = {"llm", "embedding", "image_gen"}
KNOWN_BACKENDS = {"cpu", "vulkan", "rocm", "npu", "hybrid"}
KNOWN_UNITS = {"tok/s", "img/min"}
MAX_PLAUSIBLE_VALUE = 1_000_000  # catches obvious typos (e.g. an extra zero)


class ValidationError(Exception):
    pass


def _require(cond: bool, msg: str):
    if not cond:
        raise ValidationError(msg)


def validate_report(data: dict) -> list[str]:
    """Returns a list of non-fatal warnings. Raises ValidationError on anything
    that would make the report unusable in the leaderboard.
    """
    warnings = []

    _require(isinstance(data, dict), "top level must be a JSON object")

    system = data.get("system")
    _require(isinstance(system, dict), "'system' object is required")
    cpu = system.get("cpu")
    _require(isinstance(cpu, str) and cpu.strip(), "'system.cpu' must be a non-empty string")
    for field in ("memory", "gpu", "npu", "os"):
        if not system.get(field):
            warnings.append(f"system.{field} is missing — leaderboard rows will show '—' for it")

    timestamp = data.get("timestamp")
    if timestamp:
        try:
            datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        except ValueError:
            warnings.append(f"timestamp {timestamp!r} isn't ISO 8601 — sorting may be off")
    else:
        warnings.append("no top-level 'timestamp' — submission order will be used instead")

    submitted_by = data.get("submitted_by")
    if submitted_by is not None and not (isinstance(submitted_by, str) and submitted_by.strip()):
        warnings.append("'submitted_by' should be a non-empty string (a GitHub username) if present — ignoring it")

    settings = data.get("settings")
    if settings is not None and not isinstance(settings, dict):
        warnings.append("'settings' should be an object if present — ignoring it")

    results = data.get("results")
    if not isinstance(results, dict) or not results:
        # fall back to the flat back-compat 'models' alias (llm workload only)
        models = data.get("models")
        _require(isinstance(models, dict) and models, "need a non-empty 'results' (or 'models') object")
        results = {"llm": models}

    any_ok_backend = False
    for workload, models in results.items():
        if workload not in KNOWN_WORKLOADS:
            warnings.append(f"unrecognized workload {workload!r} — the site will still show it, just ungrouped")
        _require(isinstance(models, dict) and models, f"results.{workload} must be a non-empty object")

        for model_name, backends in models.items():
            _require(isinstance(backends, dict) and backends, f"results.{workload}.{model_name} must be a non-empty object")

            for backend, entry in backends.items():
                if backend not in KNOWN_BACKENDS:
                    warnings.append(f"unrecognized backend {backend!r} in {workload}/{model_name}")
                _require(isinstance(entry, dict), f"{workload}.{model_name}.{backend} must be an object")

                if "error" in entry:
                    _require(isinstance(entry["error"], str), f"{workload}.{model_name}.{backend}.error must be a string")
                    continue

                value = entry.get("value")
                _require(
                    isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value < MAX_PLAUSIBLE_VALUE,
                    f"{workload}.{model_name}.{backend}.value must be a number between 0 and {MAX_PLAUSIBLE_VALUE} "
                    f"(got {value!r}) — if this is real, open an issue so we can raise the bound",
                )
                unit = entry.get("unit")
                if unit not in KNOWN_UNITS:
                    warnings.append(f"unrecognized unit {unit!r} in {workload}.{model_name}.{backend}")
                for optional_field in ("ttft_ms", "memory_gb"):
                    v = entry.get(optional_field)
                    if v is not None:
                        _require(isinstance(v, (int, float)) and v >= 0, f"{workload}.{model_name}.{backend}.{optional_field} must be a non-negative number")
                any_ok_backend = True

    _require(any_ok_backend, "report has no successful (non-error) backend results — nothing to show on the leaderboard")

    return warnings


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    files = [Path(f) for f in argv] if argv else sorted(RESULTS_DIR.glob("*.json"))

    if not files:
        print(f"No files to validate under {RESULTS_DIR}")
        return 0

    failed = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"FAIL {path}: not valid JSON ({e})")
            failed += 1
            continue

        try:
            warnings = validate_report(data)
        except ValidationError as e:
            print(f"FAIL {path}: {e}")
            failed += 1
            continue

        print(f"OK   {path}")
        for w in warnings:
            print(f"       warning: {w}")

    if failed:
        print(f"\n{failed}/{len(files)} file(s) failed validation.")
        return 1
    print(f"\nAll {len(files)} file(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
