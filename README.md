# ERBench Construction Machinery Industry Research v0.5 RC1

This package is a minimal benchmark task release for a single **agentic industry research** task.

It follows the same high-level release shape as `erbench-v0-5-5-rc1`:

1. `input/`
   Solver-facing task materials:
   - `description.md`
   - `reference_materials/`
2. `ENVIRONMENT.md`
   Environment guidance for running the task with any agent/runtime.
3. `judging/`
   Official rubric and script judge:
   - `rubrics.json`
   - `judge_protocol.md`
   - `judge.py`
   - `eval_runner.py`
4. `reference/`
   Non-normative leaderboard reference:
   - internal leaderboard snapshot

## What This Task Is

This is an **open-source-discovery industry research task**.

The solver receives:

- the task description
- a compact reference-material bundle

and must produce one final markdown report that:

- identifies the main industry thesis
- separates domestic and overseas logic
- performs meaningful horizontal comparison
- maps industry change to beneficiary directions or company traits
- includes risks and falsification
- includes an auditable appendix

## What This Package Includes

- one official task description
- one official rubric
- one official deterministic judge
- one internal leaderboard reference snapshot

## What This Package Does Not Include

- a gold answer
- a canonical report
- an official agent scaffold
- hidden expert notes

## Quick Start

Read the task:

```bash
cat input/description.md
```

Run the judge:

```bash
python3 judging/judge.py --submission /path/to/report.md
```

The judge prints JSON with:

- `score`
- `positive_total`
- `positive_hit`
- `negative_penalty`
- `metrics`
- `criteria`

Anything under `reference/` is **not part of the solver-facing task contract**. It is included only as a leaderboard reference snapshot.
