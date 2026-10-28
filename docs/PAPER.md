# Imi: Scope Supervision for Japanese-English Semantic Error Detection

Research pilot report | 28 October 2026 | Draft, not peer reviewed

## Abstract

We implement an offline Japanese-English translation error detector and examine whether auxiliary negation/quantifier-scope supervision improves a multilingual transformer. A pinned XLM-RoBERTa base encoder is partially fine-tuned with binary, multi-label and token error heads. Three ordinary and three scope-supervised runs are compared with frozen contextual embeddings, a cue classifier and linguistic rules. The deployment checkpoint is selected on validation data before final testing. Its mixed test F1 is 0.776, but natural-MT F1 is only 0.148, versus 0.857 on authored examples. Scope training changes mean mixed F1 from 0.747 to 0.750 across three seeds, without establishing a convincing benefit. Calibration cannot support confident positive decisions at the required empirical precision. The main result is a documented failure to generalize from easy contrasts to natural errors, rather than a validated accuracy improvement.

## 1. Motivation and related work

Small differences in negation, quantities, modality or participant roles can reverse a proposition even when a translation is fluent. For example, “not everyone passed” allows some people to have passed, whereas “nobody passed” rules that out. Likewise a deadline expressed as “by 3” permits earlier completion, unlike an exact-time instruction “at 3.” The task is consequential meaning detection, not translation generation or grammatical correction.

XLM-R provides multilingual representations rather than a task-specific guarantee of semantic equivalence [1]. COMET established learned translation-quality evaluation [2]. Joint sentence quality and error-span detection are already present in xCOMET [3], so Imi does not claim these heads as a new architecture. Tang et al. show that negation can be represented yet still mistranslated and that rephrasing complicates simple negation correspondence [4]. ACES challenges surface-overlap reliance and demonstrates the need for phenomenon-specific evaluation [5]. These works motivate a narrow controlled experiment, not a claim that Japanese-English scope detection is an unexplored field.

The research question is whether an auxiliary cue/scope-token objective improves an otherwise matched XLM-R detector on Japanese-English scope contrasts without reducing natural-MT accuracy by more than two percentage points. The scope labels here are authored template annotations, not dependency parses or independently annotated logical forms. An application-specific empirical ablation is the proposed contribution; novelty and superiority remain unproven.

## 2. Data, labels and split protocol

Natural data come from MTPEdocs-MQM [6], with published human MQM annotations of TexTra and Google outputs for 18 municipal public-information documents. Documents 001-012 are training, 013-014 validation, 015 calibration, and 016-018 final test. Both systems for a document remain together. No new independent annotation or agreement study was performed.

Major/critical semantic and terminology issues define consequential positives. Minor-only semantic rows and source-error items are excluded. Fluency-only examples are negatives for consequential meaning, not necessarily perfect translations. Generic mistranslation labels do not establish which fine-grained categories are absent: unknown categories are masked as -1. Consequently, the fine-grained natural labels are incomplete and cannot establish universal category accuracy.

Authored contrasts cover scope, modality, bounds, agents and deadlines, with small development-only examples for passive/causative, conditional, permission and other phenomena. These examples are synthetic, not expert-verified. Predicate/source families are split, but surface templates are shared across splits. This is weaker than fully unseen grammar/template evaluation and cannot rule out template memorization. Exact pair duplicates and cross-split normalized source duplicates or character-trigram near-duplicates are checked. The near-duplicate threshold is 0.85 Jaccard with length filtering; it is not a semantic equivalence detector.

After filtering there are 1,348 training pairs (899 natural, 449 authored), 412 validation (288 natural, 124 authored), 201 calibration (77 natural, 124 authored), and 296 final test (162 natural, 134 authored). The positive counts are 395, 102, 92 and 112 respectively. Preparation excluded 337 minor-semantic-only rows, two source-error rows and 325 exact pair duplicates. Two validation pairs exceed the 192-token limit and are excluded from model selection. No final test pair exceeds that limit. Dataset hashes and per-label distributions are archived.

## 3. Models and training

Both sentences are jointly tokenized by the pinned XLM-R tokenizer. Features concatenate the initial token and mean representations for source and target tokens. A 256-unit hidden layer predicts one binary logit and ten independent category logits. Separate linear token heads predict error membership and, in the experimental condition, outside/cue/scope labels. The ten categories are negation, uncertainty, quantity, agent, temporal, conditional, entity/terminology, omission, addition and other.

Only the top four encoder layers and prediction heads update; lower layers and embeddings stay frozen. There are 28,947,471 trainable parameters out of 278,049,039 total. The selected run spent 66.1 seconds in its training loop, excluding model loading and setup, with peak allocated GPU memory about 1.68 GB on the RTX 3070 Laptop. This is genuine partial encoder fine-tuning, not a frozen embedding classifier, and not full-model fine-tuning. Both variants use weighted masked binary cross-entropy and a token error loss. The scope variant adds cross-entropy on available source cue/scope labels with weight 0.25; error localization also has weight 0.25. Unknown labels are masked. AdamW rates are 2e-5 for encoder layers and 2e-4 for heads, weight decay 0.01, batch size four with four-step accumulation, three epochs, and seeds 17, 29 and 43. Best validation binary F1 selects each checkpoint.

The frozen baseline standardizes joint XLM-R features and fits balanced logistic heads with C=0.1. The original 11-feature logistic detector remains unchanged. Separate narrow linguistic rules cover partial negation, deadlines and event order. A conservative hybrid only revokes neural preserved decisions when rules flag an error; it never promotes uncertainty into confidence. This is an additional reported decision-policy ablation, not a retrained neural architecture.

## 4. Calibration and evaluation

A scalar temperature is fitted on the separate calibration split. Decision thresholds require empirical precision of at least 0.90 with at least ten examples. If a threshold is unsupported, that decision is disabled. This target is not a coverage guarantee and is not guaranteed to transfer to new domains. In the deployed model, the positive decision is disabled and the preserved threshold is 0.49. Category/token scores remain uncalibrated.

All frozen comparisons use the same final 296 pairs. Binary metrics use a 0.5 probability decision for research comparison, while three-way coverage/selective accuracy use calibrated thresholds. Thus a research F1 score is not the performance of an always-deciding deployed classifier. For cue/rule forced-binary F1 only, no finding is encoded as negative; this must not be interpreted as a successful deployed decision. Their operational no-finding cases abstain and only selective metrics describe that policy. Category metrics use known labels only and report positive support. Token overlap is evaluated at 0.5, while display spans use 0.65; displayed-span accuracy has not been separately validated. Bootstrap confidence intervals resample source/document groups, 1,000 times. There are only nine groups overall and three natural documents, so intervals are unstable and broad. The final test was not used to choose the deployment checkpoint.

## 5. Quantitative results

| Model | Mixed F1 | Natural F1 | Authored F1 | Coverage |
|---|---:|---:|---:|---:|
| ordinary-seed17 | 0.753 | 0.000 | 0.832 | 56.4% |
| scope-seed17 | 0.753 | 0.000 | 0.829 | 58.8% |
| ordinary-seed29 | 0.776 | 0.148 | 0.857 | 57.8% |
| scope-seed29 | 0.778 | 0.154 | 0.856 | 58.4% |
| ordinary-seed43 | 0.712 | 0.000 | 0.791 | 61.8% |
| scope-seed43 | 0.720 | 0.000 | 0.800 | 58.4% |
| frozen | 0.764 | 0.154 | 0.892 | 88.9% |
| cue | 0.775 | 0.000 | 0.876 | 26.7% |
| rules | 0.164 | 0.000 | 0.198 | 3.4% |
| deployed-onnx | 0.776 | 0.148 | 0.857 | 57.8% |

Ordinary mixed F1 across seeds is 0.747 +/- 0.033 (sample standard deviation); scope-aware mixed F1 is 0.750 +/- 0.029. The mean difference of 0.0034 is small relative to variability. The selected ordinary-seed29 checkpoint ties scope-seed29 on validation F1; the simpler ordinary objective was selected before testing. No hypothesis of superiority is established.

For the selected checkpoint, mixed precision is 0.736, recall 0.821 and accuracy 0.821. The confusion matrix is TN=151, FP=33, FN=20, TP=92. FPR is 0.179 and FNR is 0.179. Its grouped-bootstrap 95% F1 interval is [0.452, 0.860]. Natural-MT F1 is only 0.148: synthetic-like performance dominates the mixed headline. The frozen baseline has slightly better natural F1 (0.154) and supported-category macro-F1 (0.445) than selected fine-tuning (0.431). Neural improvement over simpler methods is therefore not demonstrated.

The calibrated deployed policy resolves 171 of 296 pairs (57.8% coverage), all as preserved, with selective accuracy 88.3%. It abstains on 125. Only 51.0% of all pairs are both resolved and correct. Abstentions are unresolved, not successful classifications. The 90% empirical calibration precision target does not carry over to this test set.

| Category | Positive test support | F1 |
|---|---:|---:|
| negation | 10 | 0.769 |
| uncertainty | 14 | 0.800 |
| quantity | 60 | 0.889 |
| agent | 3 | 0.667 |
| temporal | 4 | 0.421 |
| conditional | 0 | 0.000 |
| entity_terminology | 7 | 0.167 |
| omission | 6 | 0.000 |
| addition | 1 | 0.000 |
| other | 9 | 0.170 |

Conditional has zero positive test support, so no conditional sensitivity claim is possible. Supported-category macro-F1 excludes zero-positive categories and is not a full ten-category score. The selected token head has precision 0.675, recall 0.730 and token F1 0.702 on known supervised tokens at threshold 0.5. This does not measure explanation faithfulness or aligned bilingual phrase accuracy. Per-system, length, scope-family, contrast consistency and hybrid results are included in the machine-readable final report.

## 6. Failure analysis and deployment

The most consequential failure is weak recall of natural meaning errors despite success on conspicuous authored contrasts. Rare categories are especially weak: omission and addition F1 are zero; conditional evaluation lacks positive support. A plausible explanation is template/lexical shortcut learning plus sparse natural supervision, but this mechanism has not been causally established. Independent paraphrase and entity-substitution tests are needed. Scope auxiliary training does not solve this failure.

The known partial-negation and deadline examples are regression-tested by explicit rules. The neural category head can also return findings, but those are clearly labeled as predictions, not rule explanations. An omitted Japanese subject must not become an invented agent; the current system cannot reliably resolve such ambiguity. The interface shows uncertainty rather than a clean bill of health when a threshold or length check fails. Corrections are deliberately not generated because their semantic fidelity has not been evaluated.

The desktop runs ONNX Runtime on CPU with no remote text inference. Two dynamic uint8 export trials exceeded the prespecified numerical drift limit: maximum validation logit deviations were 2.184 with embedding and matrix quantization and 1.932 with matrix-only quantization. Both were rejected. FP32 export differs by at most 0.0000148 on the checked validation sample and takes approximately 62 ms median warm CPU inference in that export run; timing is machine/load dependent. The graph is approximately 1.11 GB. Full evaluation of the deployed graph reproduces the selected checkpoint's reported binary metrics. The model is loaded once in a persistent worker.

## 7. Post-hoc qualitative diagnostics

After final testing, 20 additional authored examples were frozen as diagnostics, not used for fitting or selection. Binary accuracy was 0.55. They are not independently verified and are not an untouched benchmark. A correct rain/cancellation paraphrase scored 0.554 for alteration (false alarm at 0.5). An incorrect translation allowing entry without returning a key scored 0.165 and was incorrectly called preserved. A prohibition substituted for Japanese permission scored 0.244 and was also incorrectly called preserved. A novel partial-scope contrast scored 0.489 for a faithful paraphrase and 0.574 for a nobody reversal, correctly straddling 0.5. These examples illustrate both successes and consequential failures.

Matched name and number substitutions changed probabilities by at most 0.021 without flipping the binary class in four comparisons. This limited invariance result does not establish robust semantic understanding: both faithful and distorted measurement examples were flagged. Exact examples and predictions are saved in research/results/posthoc-diagnostics.json; no model change followed these observations.

## 8. Limitations, ethics and next experiments

This is not a production-ready quality assessor. One natural domain, two MT systems, small rare-class support, shared authored surface templates and incomplete MQM subtype labels sharply limit conclusions. No independent human translations were separately evaluated. No independent annotator agreement, dependency-parser ablation, external COMET/xCOMET experiment or explanation-faithfulness study was completed. Long inputs abstain rather than undergoing a validated document-context analysis. A clean Windows installation has not been tested. These are outstanding tasks, not implied accomplishments.

The next study should collect legally reusable natural examples from multiple domains and systems, independently annotate specific semantic categories and spans, reserve entirely new documents and templates, and compare an external QE baseline. Since this final test has now been inspected, future tuning requires a new final test. Prospective annotators should record ambiguity and context requirements, and publish agreement before adjudication. Evaluate omission, addition and scope errors separately, including paraphrase and names/numbers counterfactuals.

Local processing reduces disclosure risk, but optional history/feedback are unencrypted. Feedback is never automatically added to research splits. Corpus annotations are CC BY-NC-SA 4.0 and exclude source-document rights; code's MIT license does not clear model redistribution. The app must not be marketed as certifying legal, medical or other consequential translations. This report and implementation were produced with AI coding assistance; authors should state their actual contribution and independently audit claims before academic submission.

## References

[1] Conneau et al. 2020. Unsupervised Cross-lingual Representation Learning at Scale. https://aclanthology.org/2020.acl-main.747/

[2] Rei et al. 2020. COMET: A Neural Framework for MT Evaluation. https://aclanthology.org/2020.emnlp-main.213/

[3] Guerreiro et al. 2024. xCOMET: Transparent Machine Translation Evaluation through Fine-grained Error Detection. https://aclanthology.org/2024.tacl-1.54/

[4] Tang et al. 2021. Revisiting Negation in Neural Machine Translation. https://aclanthology.org/2021.tacl-1.45/

[5] Moghe et al. 2025. Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets. https://aclanthology.org/2025.cl-1.4/

[6] MTPEdocs-MQM repository. https://github.com/tr4lg/MTPEdocs-MQM . Pinned commit and per-file checksums are recorded in the dataset manifest.
