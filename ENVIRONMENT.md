# Environment

This benchmark is an **agent task**, not a bundled runtime.

The solver may use any scaffold or runtime as long as it can:

- read `input/description.md`
- inspect bundled reference materials under `input/reference_materials/`
- optionally search public sources for supplementation
- produce one final markdown report

## Minimum Runtime

- OS: macOS, Linux, or Windows
- Python: `3.10+` for the local judge
- Internet access is optional but recommended if the solver wants to expand beyond the bundled reference materials

## Solver Runtime

No official scaffold is required.

The solver environment only needs enough capability to:

- read markdown and JSON files
- inspect URLs or PDFs when needed
- keep track of used sources
- write one markdown report with appendix

## Submission Convention

The judge requires one final markdown report that contains:

- core judgment
- key contention and thesis choice
- industry framework
- domestic market analysis
- overseas market analysis
- structural opportunities and beneficiary mapping
- risks and falsification
- audit appendix

The appendix must include:

- `Source Register`
- `Key Claim Map`
- `Core Numbers Table`
- `Assumption List`

## Judge Runtime

`judging/judge.py` is the official script entrypoint.

Example:

```bash
python3 judging/judge.py --submission /path/to/report.md
```

The official judge uses:

- `judging/rubrics.json`
- `judging/eval_runner.py`

It does not compare against a gold answer.
