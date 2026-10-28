# Verification - 28 October 2026

Environment: Windows 11 x64, i7-11800H, 32 GB RAM, RTX 3070 Laptop 8 GB. Node 24.22.0, Electron 42.11.18, electron-builder 26.18.0, Python 3.12.14, PyTorch 2.8.0+cu128, ONNX Runtime 1.23.2.

- 28 JavaScript unit/regression tests passed, including partial-negation scope, by/at deadlines, CSV quoting and malformed imports.
- Four research pipeline tests passed: authored correct spans, split groups, masked unknown labels and unresolved abstentions.
- Three offline CPU inference checks passed, including blocked socket connections, repeatability, UTF-16 span offsets, ten category outputs and long-input abstention.
- Six real partial XLM-R fine-tuning runs completed (ordinary/scope, seeds 17/29/43). The frozen contextual-embedding baseline completed. Training metadata, epoch losses, validation metrics and calibration records are archived in research/results/experiment-metadata.json.
- Final evaluation ran on the same 296 held-out pairs for every model. Results are in research/results/final-evaluation.json. The model generalizes poorly to natural MT; do not equate a passing implementation test with linguistic reliability.
- Source interface and final portable executable passed local analysis/highlight/navigation, input validation, JSON import, batch UI, JSON/CSV export, history save/delete and renderer isolation checks. Tests substitute temporary native-dialog fixture paths and use isolated profiles.
- The actual portable executable's standalone worker returned neural output from ordinary-seed29, probability 0.6481677889823914 for the scope regression pair, about 30.95 ms warm inference. Comparison and feedback passed. It used its bundled executable, not the development Python interpreter. See desktop-verification.json.
- The final executable returned exit code zero. Hidden-window screenshot capture may fail on this machine; that nonfunctional capture warning is recorded separately. Visible app screenshots and a live 4-fps demonstration were captured successfully.
- New interface was visually inspected in a live desktop window. Paper and poster PDFs were rendered and visually checked. The demo is an actual app recording with a preloaded model and automated examples, not fabricated predictions; first-load time is excluded.
- Two uint8 export trials failed numerical drift checks and were rejected. FP32 export max validation logit drift was 0.0000148; deployed ONNX binary evaluation matches the selected checkpoint. Approximate graph size 1.11 GB. Portable executable is about 1.61 GB with uncompressed packaging; startup extraction is noticeably slower than warm inference.

Not performed: a clean-Windows VM installation, an independent network-security audit, new human annotations/agreement, external COMET/xCOMET comparison, faithful-explanation validation, or commercial redistribution clearance. The app is unsigned. The source release excludes research weights and local user data.
