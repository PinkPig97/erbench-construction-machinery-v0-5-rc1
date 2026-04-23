#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from eval_runner import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", required=True, help="Path to markdown report")
    parser.add_argument("--rubric", help="Optional path to rubric JSON")
    parser.add_argument("--out", help="Optional output JSON path")
    args = parser.parse_args()

    submission_path = Path(args.submission)
    rubric_path = Path(args.rubric) if args.rubric else Path(__file__).resolve().with_name("rubrics.json")

    if not rubric_path.is_absolute():
        rubric_path = (Path.cwd() / rubric_path).resolve()

    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
    report = submission_path.read_text(encoding="utf-8")
    result = evaluate(report, rubric)

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
