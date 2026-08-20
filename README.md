# AMD AI Benchmarks

A community-submitted leaderboard of local AI benchmark results on AMD Ryzen AI
PCs — CPU, Vulkan, ROCm, NPU, and Hybrid, side by side, across real hardware.

**Live site: https://skywalk1411.github.io/amdaibenchmarks/** (once GitHub
Pages is enabled — see below)

## How it works

There's no server, no database, no login. Results live as plain JSON files in
[`results/`](results/), submitted by pull request. A GitHub Action validates
each submission's schema; on merge, another Action rebuilds the static
leaderboard site and deploys it to GitHub Pages. That's the whole system —
reviewable in the open, no infrastructure to run or trust.

Each report can optionally carry `submitted_by` (a GitHub username, credited
on the site next to that result) and `settings` (the exact `bench.cli`
invocation — runs, warmup, timeout, backends — that produced it). The site
shows both: the submitter's handle links to their GitHub profile, and a
"⚙ settings" toggle next to each result lets you view or copy the raw JSON
settings that were used.

The reports come from [lemonade_lab](https://github.com/skywalk1411/lemonade_lab),
a benchmarking CLI built on [Lemonade Server](https://lemonade-server.ai) that
runs the same models across every backend your Ryzen AI hardware exposes and
produces this exact JSON shape. Other tools producing compatible JSON are
welcome to submit too.

## Contributing a result

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: run `lemonade_lab`,
drop the resulting `report_*.json` into `results/`, open a PR.

## Repo layout

```
results/                    community-submitted report_*.json files
scripts/
  validate.py                  schema validation (also runs in CI on every PR)
  build_site_data.py            aggregates results/*.json -> site/data/*.json
site/                        the static leaderboard (GitHub Pages root)
  index.html
  style.css
  data/                        generated — not committed, built by CI
.github/workflows/
  validate.yml                  runs validate.py on every PR touching results/
  pages.yml                     rebuilds site/data + deploys to Pages on merge to main
```

## Running the site locally

```
python scripts/build_site_data.py
cd site && python -m http.server 8080
```

Then open http://localhost:8080.

## One-time repo setup (for the maintainer)

GitHub Pages needs to be pointed at Actions-based deployment once:
**Settings → Pages → Source → GitHub Actions**. After that, every merge to
`main` rebuilds and redeploys automatically.

## License

MIT — see [LICENSE](LICENSE). Submitted benchmark data is provided by
contributors under the same terms.
