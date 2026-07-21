#!/usr/bin/env python3
"""Validate paired test.json and ground_truth.json RAG datasets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_SCOPES = {"single_passage", "multi_section", "cross_document"}
ALLOWED_MODALITIES = {"text", "table", "chart", "mixed"}
ALLOWED_TAGS = ALLOWED_SCOPES | ALLOWED_MODALITIES | {
    "lookup",
    "comparison",
    "aggregation",
    "calculation",
    "causal",
    "procedural",
}
LEAK_FIELDS = {
    "canonical_answer",
    "answer",
    "acceptable_answers",
    "evidence",
    "relevant_evidence_ids",
    "answer_rubric",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate paired RAG evaluation dataset files."
    )
    parser.add_argument("--test", required=True, type=Path, help="Path to test.json")
    parser.add_argument(
        "--ground-truth",
        required=True,
        type=Path,
        help="Path to ground_truth.json",
    )
    return parser.parse_args()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except OSError as exc:
        raise ValueError(f"Cannot read {label}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Cannot parse {label} JSON at line {exc.lineno}, column {exc.colno}: "
            f"{exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be a JSON object.")
    return value


def require_properties(
    value: Any, properties: tuple[str, ...], location: str, errors: list[str]
) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{location} must be an object.")
        return False
    complete = True
    for property_name in properties:
        if property_name not in value:
            errors.append(f"{location} is missing '{property_name}'.")
            complete = False
    return complete


def as_list(value: Any, location: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{location} must be an array.")
        return []
    return value


def has_duplicates(values: list[Any]) -> bool:
    markers = [json.dumps(value, sort_keys=True) for value in values]
    return len(set(markers)) != len(markers)


def validate_root(root: dict[str, Any], label: str, errors: list[str]) -> None:
    require_properties(root, ("schema_version", "dataset", "cases"), label, errors)
    if root.get("schema_version") != "1.0":
        errors.append(f"{label}.schema_version must be '1.0'.")
    if "dataset" in root and not isinstance(root["dataset"], dict):
        errors.append(f"{label}.dataset must be an object.")
    if "cases" in root and not isinstance(root["cases"], list):
        errors.append(f"{label}.cases must be an array.")


def validate_test_case(case: Any, index: int, errors: list[str]) -> None:
    location = f"test.cases[{index}]"
    if not require_properties(
        case, ("case_id", "question", "question_type", "difficulty"), location, errors
    ):
        if not isinstance(case, dict):
            return

    leaked = LEAK_FIELDS.intersection(case)
    for field in sorted(leaked):
        errors.append(f"{location} leaks '{field}'.")

    question = case.get("question")
    if not isinstance(case.get("case_id"), str) or not case.get("case_id", "").strip():
        errors.append(f"{location}.case_id must be a non-empty string.")
    if not isinstance(question, str) or not question.strip():
        errors.append(f"{location}.question must be a non-empty string.")
    if case.get("difficulty") not in {"easy", "medium", "hard"}:
        errors.append(f"{location}.difficulty is invalid.")

    tags = as_list(case.get("question_type"), f"{location}.question_type", errors)
    if sum(tag in ALLOWED_SCOPES for tag in tags if isinstance(tag, str)) != 1:
        errors.append(f"{location} must have exactly one reasoning-scope tag.")
    if sum(tag in ALLOWED_MODALITIES for tag in tags if isinstance(tag, str)) != 1:
        errors.append(f"{location} must have exactly one primary-modality tag.")
    for tag in tags:
        if not isinstance(tag, str) or tag not in ALLOWED_TAGS:
            errors.append(f"{location} has unknown question_type {tag!r}.")


def validate_evidence(
    item: Any,
    location: str,
    relevant_ids: set[str],
    errors: list[str],
) -> None:
    fields = (
        "evidence_id",
        "document_id",
        "page",
        "section",
        "modality",
        "content",
        "required",
        "relevance_grade",
        "corpus_chunk_ids",
        "visual_estimate",
        "notes",
    )
    if not require_properties(item, fields, location, errors):
        if not isinstance(item, dict):
            return
    if item.get("modality") not in {"text", "table", "chart"}:
        errors.append(f"{location}.modality is invalid.")
    if type(item.get("relevance_grade")) is not int or item.get("relevance_grade") not in {1, 2}:
        errors.append(f"{location}.relevance_grade must be 1 or 2.")
    evidence_id = item.get("evidence_id")
    if evidence_id not in relevant_ids:
        errors.append(f"{location} is missing from relevant_evidence_ids.")
    if type(item.get("page")) is not int or item.get("page", 0) < 1:
        errors.append(f"{location}.page must be a positive integer.")
    if not isinstance(item.get("required"), bool):
        errors.append(f"{location}.required must be a boolean.")
    if not isinstance(item.get("visual_estimate"), bool):
        errors.append(f"{location}.visual_estimate must be a boolean.")
    as_list(item.get("corpus_chunk_ids"), f"{location}.corpus_chunk_ids", errors)


def validate_truth_case(case: Any, index: int, errors: list[str]) -> None:
    location = f"ground_truth.cases[{index}]"
    fields = (
        "case_id",
        "canonical_answer",
        "acceptable_answers",
        "answer_constraints",
        "relevant_evidence_ids",
        "evidence",
        "answer_rubric",
    )
    if not require_properties(case, fields, location, errors):
        if not isinstance(case, dict):
            return

    answer = case.get("canonical_answer")
    if not isinstance(case.get("case_id"), str) or not case.get("case_id", "").strip():
        errors.append(f"{location}.case_id must be a non-empty string.")
    if not isinstance(answer, str) or not answer.strip():
        errors.append(f"{location}.canonical_answer must be a non-empty string.")
    as_list(case.get("acceptable_answers"), f"{location}.acceptable_answers", errors)

    relevant_values = as_list(
        case.get("relevant_evidence_ids"),
        f"{location}.relevant_evidence_ids",
        errors,
    )
    relevant_ids = {value for value in relevant_values if isinstance(value, str)}
    if len(relevant_ids) != len(relevant_values):
        errors.append(f"{location}.relevant_evidence_ids must contain unique strings.")

    evidence = as_list(case.get("evidence"), f"{location}.evidence", errors)
    if not evidence:
        errors.append(f"{location}.evidence must not be empty.")
    evidence_ids = [
        item.get("evidence_id") for item in evidence if isinstance(item, dict)
    ]
    if has_duplicates(evidence_ids):
        errors.append(f"{location} evidence_id values must be unique.")
    for relevant_id in relevant_ids:
        if relevant_id not in evidence_ids:
            errors.append(f"{location} references unknown evidence '{relevant_id}'.")
    for evidence_index, item in enumerate(evidence):
        validate_evidence(
            item,
            f"{location}.evidence[{evidence_index}]",
            relevant_ids,
            errors,
        )

    rubric = case.get("answer_rubric")
    rubric_location = f"{location}.answer_rubric"
    require_properties(
        rubric,
        ("required_points", "optional_points", "disallowed_claims", "grading_notes"),
        rubric_location,
        errors,
    )
    if isinstance(rubric, dict):
        required_points = as_list(
            rubric.get("required_points"), f"{rubric_location}.required_points", errors
        )
        as_list(rubric.get("optional_points"), f"{rubric_location}.optional_points", errors)
        as_list(
            rubric.get("disallowed_claims"),
            f"{rubric_location}.disallowed_claims",
            errors,
        )
        if not required_points:
            errors.append(f"{rubric_location}.required_points must not be empty.")


def validate(test: dict[str, Any], truth: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_root(test, "test", errors)
    validate_root(truth, "ground_truth", errors)

    if test.get("dataset") != truth.get("dataset"):
        errors.append("dataset metadata must be identical in both files.")

    test_cases = test.get("cases") if isinstance(test.get("cases"), list) else []
    truth_cases = truth.get("cases") if isinstance(truth.get("cases"), list) else []
    if not test_cases:
        errors.append("test.cases must not be empty.")
    if len(test_cases) != len(truth_cases):
        errors.append("The files must contain the same number of cases.")

    test_ids = [case.get("case_id") if isinstance(case, dict) else None for case in test_cases]
    truth_ids = [case.get("case_id") if isinstance(case, dict) else None for case in truth_cases]
    if has_duplicates(test_ids):
        errors.append("test case_id values must be unique.")
    if has_duplicates(truth_ids):
        errors.append("ground-truth case_id values must be unique.")
    if test_ids != truth_ids:
        errors.append("case_id values and order must match across files.")

    for index, case in enumerate(test_cases):
        validate_test_case(case, index, errors)
    for index, case in enumerate(truth_cases):
        validate_truth_case(case, index, errors)
    return errors


def main() -> int:
    args = parse_args()
    try:
        test = load_json(args.test, "test")
        truth = load_json(args.ground_truth, "ground truth")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors = validate(test, truth)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Dataset validation passed: {len(test['cases'])} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
