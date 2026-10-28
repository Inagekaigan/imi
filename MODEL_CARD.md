# Imi XLM-R research model, 0.2.0

**Natural-error generalization failed. Do not treat this model as a dependable translation checker.**

Architecture: pinned XLM-R base with top four encoder layers fine-tuned, binary + ten multi-label classifiers and token error localization. Deployed checkpoint: ordinary-seed29, selected on validation F1 before final testing. Scope supervision was studied separately across three seeds; no convincing benefit established.

Training data: 899 natural MT pairs with existing human MQM annotations plus 449 authored contrasts. Natural annotations map major/critical semantic issues to positives; fine-grained unknown labels are masked. Source documents are municipal public information. No new human annotation or agreement study was performed.

Independent final evaluation: 296 pairs, 162 natural and 134 authored. The deployed binary head has F1 **0.776 mixed, 0.148 natural, 0.857 authored**. The mixed score is not representative of real-world reliability. Supported-category macro-F1 is 0.431. Omission/addition F1 is zero; conditional has no positive test support. Grouped 95% mixed-F1 interval: [0.452, 0.860].

Calibration: scalar temperature on a separate 201-pair split. The empirical 90% positive-precision target was not supported, so confident altered decisions are disabled. Preserved threshold 0.49 gives test coverage 57.8% and selective accuracy 88.3%; 125/296 are unresolved. Only 51.0% of all test pairs are resolved correctly. A preserved prediction is not certification. Category and token probabilities are uncalibrated.

Token-head F1 at research threshold 0.5 is 0.702 on known labels. The UI uses 0.65 for display, without a separately validated display-span metric. Highlights are not category-specific alignments or verified explanations. Source labels are sparse; no invented source alignment is claimed. Rule evidence is always identified separately.

Deployment: actual local ONNX CPU inference; 192-token combined limit, no truncation. FP32 chosen after two uint8 exports exceeded numerical drift limits. Approximately 1.11 GB graph; 62 ms median warm CPU time in the recorded validation check, excluding cold load and tokenization. Runtime and timings vary by machine. See manifest hashes and full report.

License: Imi-authored code has no public reuse license; pretrained base MIT, natural annotations CC BY-NC-SA 4.0 with source rights excluded. The research checkpoint is not declared commercially cleared or MIT. Read research/DATA_LICENSES.md before redistribution.

Known gaps: natural semantic errors, unfamiliar domains, complex referents, conditional/causative scope, long documents, legitimate paraphrases, entity substitutions, external QE comparison, independent annotation, clean-Windows testing and faithful explanations. No correction generator is provided.

See docs/PAPER.md, research/PROTOCOL.md, research/results/final-evaluation.json and research/data/dataset-report.json for the actual evidence and reproducibility instructions.
