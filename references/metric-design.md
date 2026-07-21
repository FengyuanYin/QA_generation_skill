# Metric-oriented design

## Retrieval metrics

### Recall, precision, and F1

Annotate the complete set of answer-bearing evidence units for each case. Mark indispensable units as `required`. Evaluate retrieved corpus chunks by mapping them to evidence IDs, then compute precision and recall at declared cutoffs such as 1, 3, 5, and 10. Do not inflate the relevant set with background context: it makes weak retrieval appear better and corrupts precision.

For multi-section and cross-document questions, include each independently required unit. Report both ordinary evidence recall and all-required-evidence success so partial retrieval does not look complete.

### MRR

MRR uses the rank of the first grade-2 relevant result. Include direct answer-bearing evidence and avoid multiple redundant copies of the same fact unless each copy is legitimately relevant. Use questions with discriminative wording so the first relevant rank reflects retrieval quality rather than annotation ambiguity.

### MAP

MAP requires a defensible set of all relevant evidence items. Include multiple relevant items only when each independently contributes or independently answers the question. Preserve graded relevance so an evaluator may also compute nDCG, but compute standard AP from grades greater than zero only if that policy is declared in the evaluation report.

## Generation metrics

### ROUGE and BLEU

Use concise canonical answers and equivalent accepted variants. Favor stable terminology, named entities, values, units, and short relationships. These lexical metrics are unreliable for long, highly abstractive answers; do not design the entire dataset around them. Report the best score across accepted references when the evaluator supports multiple references.

### LLM-as-judge

Provide atomic `required_points`, optional enrichment, prohibited claims, and case-specific notes. Ask the judge to score correctness, completeness, grounding, relevance, and concision separately. Keep the source evidence hidden from the tested generator only if the RAG system supplies its own retrieved context; supply the gold evidence to the judge for grounded adjudication.

Recommended judge scale:

- 4: Fully correct, complete, grounded, and concise.
- 3: Correct core answer with a minor omission or harmless imprecision.
- 2: Partially correct but missing a required point or containing a material ambiguity.
- 1: Mostly incorrect, weakly grounded, or seriously incomplete.
- 0: Incorrect, unsupported, contradictory, or no answer.

Use deterministic exact/numeric checks before an LLM judge when possible. Periodically calibrate judge prompts against human-reviewed samples and randomize candidate order for pairwise comparisons.

## Coverage design

Create cases that expose different failure modes:

| Case design | Primary diagnostic value |
| --- | --- |
| Single exact passage | Baseline retrieval and concise answer accuracy |
| Multiple relevant passages | Recall, precision, MAP, evidence deduplication |
| Multi-section synthesis | Complete evidence recall and compositional answering |
| Cross-document synthesis | Corpus routing and source reconciliation |
| Table lookup/calculation | Structured retrieval, headers, units, arithmetic |
| Chart interpretation | Visual retrieval, legend/axis reading, approximation |
| Lexically confusable topics | Ranking quality, precision, MRR |

Do not add adversarial distractors to `ground_truth.json` unless the evaluation harness explicitly consumes them. Natural confounders already present in the corpus are preferable because they preserve corpus fidelity.

## Reporting

Report metric cutoffs, chunk-to-evidence mapping policy, treatment of relevance grade 1, aggregation method (micro/macro), unanswered cases, and confidence intervals or sample counts. Break down scores by reasoning scope and modality; an aggregate score can hide failures on charts or cross-document questions.
