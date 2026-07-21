# RAG Evaluation Dataset Generator

This skill generates metric-ready RAG evaluation datasets from one or more PDF documents. It supports text, tables, charts, multi-section evidence, and cross-document evidence.

The dataset language follows the user's request. When no language is specified, use the primary language of the source documents. Keep questions and answers in the same language unless cross-lingual evaluation is explicitly requested.

## Output

Generate two files:

- `test.json`: questions, non-leaking metadata, question types, and difficulty labels.
- `ground_truth.json`: canonical answers, accepted variants, evidence judgments, retrieval relevance labels, and LLM judge rubrics.

Use the structures in `templates/` and follow the complete workflow in `SKILL.md`.

## Validation

```bash
python scripts/validate_dataset.py --test <path-to-test.json> --ground-truth <path-to-ground_truth.json>
```

Structural validation does not replace manual source verification. Audit every chart and table item and verify sampled text evidence against the rendered PDFs.
