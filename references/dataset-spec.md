# Dataset specification

## Contents

1. File contracts
2. Test case schema
3. Ground-truth schema
4. Evidence representation
5. Quality gates

## File contracts

Both JSON files are objects with `schema_version`, `dataset`, and `cases`. The `dataset` object contains `name`, `language`, `source_documents`, `created_at`, and optional generation notes. Use ISO 8601 for `created_at` and stable, filename-independent document IDs when possible.

`test.json` is safe to send to the system under evaluation. It must not contain canonical answers, acceptable answers, evidence text, evidence IDs, source pages, section names that reveal the answer, judge rubrics, or relevance labels.

`ground_truth.json` is evaluator-only. It must contain exactly one matching record for every test case and no unmatched records.

## Test case schema

Each `test.json` case contains:

```json
{
  "case_id": "q-0001",
  "question": "A self-contained question in the selected dataset language",
  "question_type": ["single_passage", "text"],
  "difficulty": "medium"
}
```

Allowed `question_type` tags are:

- Reasoning scope: `single_passage`, `multi_section`, `cross_document`
- Primary modality: `text`, `table`, `chart`, `mixed`
- Optional operation: `lookup`, `comparison`, `aggregation`, `calculation`, `causal`, `procedural`

Use `easy`, `medium`, or `hard` for difficulty. Difficulty reflects evidence discovery and reasoning, not obscure wording.

## Ground-truth schema

Each `ground_truth.json` case contains:

```json
{
  "case_id": "q-0001",
  "canonical_answer": "Concise complete answer.",
  "acceptable_answers": ["Equivalent answer form."],
  "answer_constraints": {
    "numeric_tolerance": null,
    "units": null,
    "case_sensitive": false
  },
  "relevant_evidence_ids": ["doc-a:p12:fig3"],
  "evidence": [],
  "answer_rubric": {
    "required_points": ["Fact that must be present"],
    "optional_points": [],
    "disallowed_claims": ["A specific misleading or unsupported claim"],
    "grading_notes": "Judge correctness, completeness, grounding, and concision."
  }
}
```

Make `canonical_answer` concise but complete enough for ROUGE and BLEU. Phrase it naturally instead of copying long source passages. Keep `acceptable_answers` short and genuinely equivalent. Use `numeric_tolerance` for rounded or visually estimated values; otherwise use `null`.

The LLM judge rubric must be case-specific. `required_points` should decompose the answer into atomic claims. Use `disallowed_claims` for plausible but materially wrong interpretations, wrong units, reversed comparisons, or unsupported extrapolations. Do not reward verbosity.

## Evidence representation

Every evidence object contains:

```json
{
  "evidence_id": "doc-a:p12:fig3",
  "document_id": "doc-a",
  "page": 12,
  "section": "Results",
  "modality": "chart",
  "content": "Figure 3. Series A rises from 12% in 2022 to 18% in 2024.",
  "required": true,
  "relevance_grade": 2,
  "corpus_chunk_ids": [],
  "visual_estimate": false,
  "notes": "Values are printed as data labels."
}
```

Use PDF page numbers as displayed by the viewer. If printed page labels differ, record the printed label in `notes`. `modality` is one of `text`, `table`, or `chart`. For a mixed question, include separate evidence objects rather than collapsing modalities.

An `evidence_id` identifies a semantic source region, not an arbitrary generated answer. Recommended form: `<document_id>:p<page>:<region>`. Keep IDs stable across repeated generation runs.

For tables, represent only the answer-bearing slice but include necessary headers, labels, units, and footnotes. For charts, never infer precise values from pixels when the chart supports only an approximate comparison; phrase the question and answer accordingly.

## Quality gates

Accept a case only if all answers are yes:

1. Is the question self-contained and unambiguous?
2. Is there one stable answer under the stated scope?
3. Does the answer express a useful, information-dense fact or relationship?
4. Is every required answer claim directly supported by cited evidence?
5. Are all required evidence units included, and are irrelevant units excluded?
6. Can a retrieval miss or ranking error be measured from the evidence labels?
7. Can generation quality be judged from the canonical answer and atomic rubric?
8. Is the item distinct from all other questions?
9. Is no evidence drawn from an excluded section or boilerplate?
10. For visual items, was the rendered page manually verified?

Reject cases with unstable interpretation, external-knowledge dependence, vague pronouns, excessive setup, compound questions with separable answers, answer leakage, or citations that merely mention the topic.
