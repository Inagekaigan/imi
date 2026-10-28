# Consequential meaning-error annotation

Annotate the Japanese original and English translation together. Ignore awkwardness, punctuation and stylistic differences unless they change the proposition. Mark the smallest spans sufficient to show a semantic change. Do not invent an omitted Japanese subject or resolve an ambiguous referent without context. Multiple labels may apply.

| Label | Consequential difference | Distinction |
|---|---|---|
| negation | Polarity or quantifier scope changes | Not everyone does X is not nobody does X. |
| uncertainty | Possibility, probability, certainty, obligation or permission changes | May do, must do and may not do are not interchangeable. |
| quantity | Number, bound, approximation, comparison or unit changes | At least 10, at most 10 and exactly 10 differ. |
| agent | Agent, patient, recipient or causative role changes | Preserve who acts on whom; passive voice alone is not an error. |
| temporal | Event order, deadline, date or duration changes | By 3 permits earlier completion; at 3 specifies a time. |
| conditional | Antecedent, consequent or causal relation changes | If A then B does not imply if B then A. |
| entity_terminology | A name, place or domain term changes its referent | A legitimate alternate spelling is not an error. |
| omission | Material information is absent in English | Highlight the omitted source phrase; target span may be empty. |
| addition | English asserts unsupported information | Highlight the added target phrase; source span may be empty. |
| other | Clear consequential change outside known labels | Record an explanation; do not force a specific label. |

For prospective independent annotation: two bilingual annotators work blind to model output and each other's labels. Allow uncertain/context-needed labels. Adjudicate disagreements only after calculating raw agreement, per-label Cohen's kappa and span-overlap F1 on unadjudicated judgments. Report sample size, prevalence and annotator qualifications. These measurements have **not** been performed in this pilot.

Existing MQM annotations are mapped conservatively: major/critical accuracy or terminology issues are positive; minor-only semantic issues are excluded, source-error items excluded, fluency-only items negative for this task. Generic mistranslation does not reveal all fine-grained labels, so unknown category labels are masked as -1. This mapping is not new human verification of the Imi taxonomy. Source localization supervision is available only where annotated (particularly omissions); missing alignments are not treated as negative source spans.

No corrections are generated in this release: an unvalidated suggested translation could introduce new errors. Category explanation templates state the model's prediction and limitations rather than claiming to explain its internal reasoning.
