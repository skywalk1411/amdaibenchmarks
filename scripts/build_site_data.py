#!/usr/bin/env python3
"""Aggregates results/*.json into the static data files the site reads.

Unlike lemonade_lab's leaderboard server (a live FastAPI + SQLite app), this
has no backend at all — GitHub Pages serves plain files. Filtering by
workload/model happens client-side in site/app.js against the single combined
leaderboard.json this script produces.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
DATA_DIR = ROOT / "site" / "data"


def _results_view(report: dict) -> dict:
    if report.get("results"):
        return report["results"]
    if report.get("models"):
        return {"llm": report["models"]}
    return {}


def build():
    leaderboard_rows = []
    report_summaries = []

    for path in sorted(RESULTS_DIR.glob("*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        report_id = path.stem
        system = report.get("system", {})

        report_summaries.append({
            "id": report_id,
            "file": path.name,
            "label": report.get("label", report_id),
            "timestamp": report.get("timestamp"),
            "cpu": system.get("cpu"),
            "gpu": system.get("gpu"),
            "npu": system.get("npu"),
            "memory": system.get("memory"),
            "os": system.get("os"),
        })

        for workload, models in _results_view(report).items():
            for model_name, backends in models.items():
                for backend, entry in backends.items():
                    if entry.get("error") or entry.get("value") is None:
                        continue
                    leaderboard_rows.append({
                        "report_id": report_id,
                        "workload": workload,
                        "model": model_name,
                        "backend": backend,
                        "value": entry["value"],
                        "unit": entry.get("unit", "tok/s"),
                        "ttft_ms": entry.get("ttft_ms"),
                        "memory_gb": entry.get("memory_gb"),
                        "cpu": system.get("cpu"),
                        "gpu": system.get("gpu"),
                        "npu": system.get("npu"),
                        "memory": system.get("memory"),
                        "timestamp": report.get("timestamp"),
                    })

    leaderboard_rows.sort(key=lambda r: r["value"], reverse=True)
    report_summaries.sort(key=lambda r: r["timestamp"] or "", reverse=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "leaderboard.json").write_text(json.dumps(leaderboard_rows, indent=2), encoding="utf-8")
    (DATA_DIR / "reports.json").write_text(json.dumps(report_summaries, indent=2), encoding="utf-8")

    print(f"Wrote {len(leaderboard_rows)} leaderboard rows from {len(report_summaries)} report(s) to {DATA_DIR}")


if __name__ == "__main__":
    build()
