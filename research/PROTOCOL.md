# Imi neural pilot: preregistered experiment protocol

This protocol is written before neural training or inspection of final-test predictions. It is a local research record, not a registration with an external registry.

## Question and hypothesis

Does an auxiliary token-level negation/quantifier-scope objective improve Japanese–English semantic-error detection over ordinary XLM-R sentence-pair fine-tuning, without materially increasing false alarms on human-annotated non-semantic-error translations?

H1: scope supervision improves macro-F1 and contrastive consistency on held-out scope constructions. H2: it does not decrease natural-MT binary accuracy by more than 2 percentage points. These are exploratory pilot hypotheses, not novelty claims. An adequately powered independent follow-up is needed.

## Comparisons

1. Existing trained cue-feature logistic baseline, frozen as v0.1.0.
2. Explicit linguistic rules, evaluated separately.
3. Frozen XLM-R embeddings with logistic heads.
4. XLM-R sentence-pair fine-tuning with binary and multi-label heads plus an error-span head.
5. The same model, data, optimization and seeds, with an additional scope-token objective.
6. A conservative hybrid of neural predictions and rules; disagreement triggers uncertainty rather than silently overwriting the neural output.

The pretrained word embedding table can be frozen for memory efficiency; encoder layers and prediction heads must actually update. Report trainable parameter count. Do not call a frozen embedding classifier a fine-tuned transformer.

## Data and label fidelity

Use MTPEdocs-MQM's naturally occurring outputs of TexTra and Google with published human issue annotations. Major/critical Accuracy, Terminology, or Non-translation issues are consequential-error positives; examples with only minor semantic issues are excluded from binary training/evaluation rather than mislabeled as fully correct. Fluency-only changes may be negative for consequential semantic error under this protocol, not for all translation-quality errors. Source-error annotations are excluded.

Preserve upstream error types. Generic mistranslation annotations do not establish the absence of negation/agent/quantity errors: specific unknown category labels are masked, not converted to negative labels. Evaluate known labels only and report their support. Dataset-level category proxies must not be described as newly human-verified Imi labels. No independent annotators have yet been recruited.

Supplement with explicitly marked authored contrastive examples. These are synthetic and not expert-verified. Use whole template families as groups; all variants of one Japanese source remain in one split. Human annotations and natural errors must be reported separately from constructed challenges.

MTPEdocs document IDs 001–012: training; 013–014: model selection; 015: calibration; 016–018: final test. Both MT systems for a document share its split. Exact and near-duplicate Japanese sources crossing splits are removed from later splits; retain an exclusion audit. Repeat rows within the same source/translation pair are deduplicated.

## Measurement

Checkpoint selection uses validation binary F1 only. Fit scalar temperature on calibration data, and choose altered/preserved thresholds on that data subject to a minimum support and empirical precision target. If no threshold meets the target, abstain; never invent a confidence guarantee. Model scores remain distribution-dependent even after calibration.

Freeze model/checkpoint IDs, thresholds, data hashes, and experiment configuration before unsealing the test set. Run final evaluation once for all predeclared models. Do not tune on test failures. Further changes require a new test set or must be labeled post-hoc development.

Report binary precision/recall/F1, confusion matrix, FPR/FNR, multi-label macro-F1 with known-label support, per-category results, span token F1, Brier score/ECE, abstention coverage, selective accuracy, and unconditional accuracy where abstentions count as unresolved rather than correct. Report natural/synthetic and domain/system breakdowns. Bootstrap by source/document group, not by duplicate rows. Repeat important comparisons with seeds 17, 29, and 43 where computation permits; incomplete runs remain explicitly incomplete.

Do not describe auxiliary labels derived from templates as human grammatical scope annotation. Token predictions are model-generated localization; linguistic evidence cues must be labeled separately. Explanation templates describe predicted classes and must not be advertised as faithful causal explanations of hidden representations.

## External comparisons and limits

COMET/xCOMET and ACES/SPAN-ACES establish relevant prior art. Exact external baseline runs require their weights, license compliance, and sufficient hardware; a literature citation is not an executed comparison. Japanese dependency-parser ablations, additional domains, independent annotators, and clean-Windows testing remain unverified until performed. Agreement scores cannot be estimated from one annotation per item.
