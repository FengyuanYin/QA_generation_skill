---
name: generate-rag-evaluation-dataset
description: Generate high-value multilingual RAG evaluation datasets from one or more PDFs, including text, tables, charts, and cross-section or cross-document evidence. Use when Codex must inspect PDF content and produce paired test.json and ground_truth.json files designed to evaluate retrieval Recall, Precision, F1, MRR, MAP, answer ROUGE/BLEU, and LLM-as-judge quality.
---

# Generate a RAG Evaluation Dataset

Create an evaluation dataset from the supplied PDFs. Use the language requested by the user; otherwise follow the primary language of the source material. Keep each question and its answer in the same language unless the user explicitly requests cross-lingual evaluation. Produce exactly two required dataset files: `test.json` and `ground_truth.json`. Preserve traceability to the source PDFs and make the dataset useful for both retrieval and answer-generation evaluation.

## Read the specification

Read [references/dataset-spec.md](references/dataset-spec.md) before generating data. Read [references/metric-design.md](references/metric-design.md) when choosing question types, evidence annotations, or dataset balance.

Use [templates/test.json](templates/test.json) and [templates/ground_truth.json](templates/ground_truth.json) as structural examples, not as source data.

## Workflow

1. Inventory every PDF and assign a stable `document_id`. Record titles and page counts.
2. Extract page text while retaining page numbers, section headings, table structure, figure captions, labels, legends, axes, units, and footnotes. Use OCR or visual page inspection when embedded text is incomplete or when a chart carries answer-bearing information.
3. Exclude front matter, prefaces, forewords, disclaimers, headers, footers, tables of contents, bibliographies/references, copyright notices, and other boilerplate. Do not derive questions or answer evidence from excluded material.
4. Build an evidence map before writing questions. Give each answer-bearing passage, table region, or figure region a stable `evidence_id`. Preserve its `document_id`, page, section, modality, and a concise verbatim or faithfully serialized excerpt.
5. Draft candidate questions in the selected dataset language. Favor facts, comparisons, relationships, constraints, causes, procedures, and quantitative results that matter to a knowledgeable reader.
6. Retain a candidate only when it has a clear question, a unique or stable answer, high information density, and sufficient cited evidence. Reject trivia, vague prompts, redundant paraphrases, opinion questions, and questions answerable from document titles or boilerplate alone.
7. Include a deliberate mix of single-passage, multi-section, cross-document, table-based, and chart-based questions when supported by the PDFs. Never force a category that the sources cannot support.
8. Write `test.json` without answers or evidence leakage. Write every corresponding answer, evidence judgment, acceptable variant, and scoring rubric to `ground_truth.json` under the same `case_id`.
9. Run `scripts/validate_dataset.py` and fix every error. Manually audit all chart/table items and a sample of text items against the rendered PDF pages.

## Grounding rules

- Derive every answer solely from included source evidence.
- Cite all evidence needed to answer the question; do not cite merely related passages.
- Split evidence into independently retrievable units. Mark each unit `required: true` only when omitting it makes the answer incomplete or unsupported.
- Use `relevance_grade: 2` for directly answer-bearing evidence, `1` for useful supporting evidence, and `0` only for explicit hard negatives when requested. Do not place grade-0 items in `relevant_evidence_ids`.
- For multi-hop questions, state the evidence combination logic in `answer_rubric`. Ensure the answer genuinely requires all marked-required evidence.
- For tables, serialize headers, row labels, values, units, and footnotes needed for interpretation.
- For charts, capture the chart title, series, axes, legend, units, relevant values or trends, and whether a value is exact or visually estimated. Set `visual_estimate: true` when appropriate and define an accepted tolerance.
- For cross-document questions, avoid contradictions caused by different editions, populations, dates, definitions, or units. State necessary scope in the question.
- Prefer one canonical answer. Add `acceptable_answers` only for semantically equivalent wording, formatting, unit conversion, or an explicit numeric tolerance.

## Dataset composition

Unless the user specifies another distribution, target:

- 40-60% single-passage text questions.
- 15-25% multi-section questions.
- 10-20% cross-document questions when multiple documents support them.
- 15-25% table or chart questions, with at least some chart-dependent items when answer-bearing charts exist.

Tag overlapping properties independently in `question_type`; totals need not sum to 100%. Avoid duplicate answers and near-duplicate questions. Balance easy direct retrieval with compositional cases while prioritizing source value over quotas.

## Output requirements

- Use UTF-8 JSON with two-space indentation.
- Keep `case_id` unique and identical across both files.
- Keep the case order identical across both files.
- Put only evaluation inputs and non-leaking tags in `test.json`.
- Put canonical answers, acceptable answers, evidence, retrieval relevance judgments, and LLM judge rubrics in `ground_truth.json`.
- Copy schema and generation metadata into both file roots and set `schema_version` to `1.0`.
- Do not invent source chunk IDs. If the target corpus already has chunk IDs, add them to evidence as `corpus_chunk_ids`; otherwise use stable dataset `evidence_id` values and document how the evaluation harness maps corpus chunks to them.

## Validate

Run:

```bash
python scripts/validate_dataset.py --test <path-to-test.json> --ground-truth <path-to-ground_truth.json>
```

Treat successful structural validation as necessary but insufficient. Complete the source audit and report dataset counts by question type, modality, evidence span, and document coverage.
