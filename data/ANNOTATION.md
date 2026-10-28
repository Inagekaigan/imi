# Annotation protocol

This file describes the original four-category feature baseline. The neural pilot's expanded taxonomy, unknown-label policy and prospective human annotation procedure are in `research/ANNOTATION_GUIDE.md`.

Use only texts you have permission to process and distribute. Keep private corpora under `private-data/`, which is ignored by Git.

For every pair, assign zero or more labels:

- `negation`: the polarity of a proposition is reversed, added, or removed.
- `uncertainty`: epistemic strength changes materially (for example, possible → certain).
- `quantity`: a number, range, comparison, or limit changes materially.
- `agent`: a different entity is presented as performing the action.

Do not label stylistic or grammatical differences unless they change one of these meanings. Keep unrelated semantic errors in a separate annotation field rather than pretending they are negative examples for overall accuracy. A faithful paraphrase can have very different wording.

Use two Japanese–English bilingual annotators, followed by adjudication. Preserve uncertainty and annotate excluded/ambiguous cases separately. Store source/translation evidence spans as optional `japaneseSpans` and `englishSpans` arrays of UTF-16 `[start,end]` offsets; the current classifier does not train on these fields, but a future span model can.

Required training schema:

```json
{"id":"unique-id","group":"source-document-id","split":"train","japanese":"...","english":"...","labels":["negation"]}
```

Use `split: "test"` for held-out evaluation. Keep all sentence variants from one document and their augmentations in the same group/split. Do not use a real held-out test set to tune features or thresholds. For research-scale work, add a separate development set and retain a frozen external test set; the bundled trainer currently supports only train/test.

The bundled `synthetic.jsonl` is generated from authored templates, not gathered from real translation errors. It is licensed under the repository's MIT license.
