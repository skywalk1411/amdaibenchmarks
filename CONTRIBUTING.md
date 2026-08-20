# Contributing a result

1. Run [lemonade_lab](https://github.com/skywalk1411/lemonade_lab) against your
   AMD Ryzen AI PC:

   ```
   python -m bench.cli
   ```

   This writes a `report_*.json` file to `reports/`. Run it across as many
   backends as your hardware supports (CPU, Vulkan, ROCm, NPU, Hybrid) for the
   most useful comparison — `python -m bench.cli --backends cpu vulkan rocm npu hybrid`.

   Or skip steps 2-4 below and let `lemonade_lab` do them for you:
   `python -m bench.cli --submit` clones/validates/commits/pushes a
   `submit/<slug>` branch to this repo and prints a compare URL to open the
   PR from — see its README for details, including how it credits your
   GitHub username via `submitted_by`.

2. Copy that file into `results/` in this repo. Rename it to something
   descriptive: `<cpu-model>-<what-it-covers>.json`, e.g.
   `ryzen-ai-9-hx370-llm-vulkan-npu.json`. Lowercase, hyphens, no spaces.

3. Open a pull request adding just that file. In the PR description, mention:
   - What machine/BIOS settings you ran it on (especially UMA/VRAM split, if
     you've changed it from default — it materially affects NPU/CPU results).
   - Anything unusual about the run (thermal throttling, background load, etc.)

4. A GitHub Action validates the file automatically (`python scripts/validate.py`)
   and reports back on the PR. Fix anything it flags before requesting review.

## What gets rejected

- Malformed JSON, or missing required fields (see `scripts/validate.py` for the
  exact rules).
- Implausible values (the validator catches obvious typos, but a maintainer
  will also sanity-check numbers against known hardware before merging).
- Files that aren't real benchmark output — this is a real-hardware leaderboard,
  not a synthetic one.

## Multiple runs from the same machine

Totally fine — submit a new file each time (e.g., after a driver update, or
covering a model/backend you didn't test before). Don't overwrite an old
result unless it was wrong; historical results are useful for tracking
driver/backend improvements over time.

## Report format

Files must match the JSON shape `lemonade_lab`'s `bench/report.py` produces:
a `system` object (cpu/memory/gpu/npu/os) and a `results` object keyed by
workload (`llm`, `embedding`, `image_gen`), then model name, then backend,
each holding `{value, unit, ttft_ms, memory_gb}` or `{error}`. Other tools
producing this exact shape are welcome too.

Two optional top-level fields the site knows how to display:

- `submitted_by` — your GitHub username, credited on the leaderboard next to
  your results (linked to your profile). `lemonade_lab --submit` fills this
  in automatically (see its README); if you're submitting by hand, feel free
  to add it yourself.
- `settings` — the benchmark run's own settings (e.g. `runs`, `warmup`,
  `timeout`, `backends`), shown behind a "⚙ settings" toggle on each result so
  others can see (and copy) exactly what produced a given number.

Neither field is required — `scripts/validate.py` only warns if they're
present but malformed, it won't reject a submission that omits them.
