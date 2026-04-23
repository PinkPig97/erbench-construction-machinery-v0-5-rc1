# Judge Protocol

This task uses a **deterministic rubric runner** as the official scoring scheme.

There is:

- no gold answer
- no single canonical report
- no holistic LLM judge

Instead, the official judge combines:

1. structural parsing of the submission
2. deterministic metric extraction
3. weighted rubric aggregation

## Judge Goal

`judging/judge.py` is the official entrypoint. It delegates to:

- `judging/eval_runner.py`

The runner:

1. parses report structure
2. extracts appendix tables
3. computes auditable metric signals
4. evaluates each rubric criterion against a named signal
5. aggregates weights into a final score

## Scoring Rule

- `positive_total` = sum of all positive rubric weights
- `positive_hit` = sum of positive weights that passed
- `negative_penalty` = sum of absolute negative weights that triggered
- `net = positive_hit - negative_penalty`
- `score = max(net / positive_total, 0.0)`

## Output Format

The judge outputs JSON with:

- `score`
- `net`
- `positive_total`
- `positive_hit`
- `negative_penalty`
- `metrics`
- `criteria`

Each criterion result includes:

- `id`
- `category`
- `polarity`
- `weight`
- `criterion`
- `runner_signal`
- `signal_value`
- `passed_or_triggered`

## Important Limitation

This is a benchmark judge, not universal ground truth.

Scores should be interpreted as:

- benchmark-relative quality estimates under this task definition

not as an absolute measure of all possible industry research quality.
