# Security

Imi processes untrusted sentence text without interpreting it as markup or executable code. The desktop renderer is isolated and sandboxed, with a restrictive content security policy. Main-process IPC validates the caller; file selection uses native dialogs. Imports are size- and shape-limited. Network requests are blocked at runtime.

The local neural worker loads ONNX and tokenizer files directly and does not invoke remote inference or downloads. Automated checks disable socket connections during Python inference; this is not an independent OS-level network audit. Explicit setup/download scripts require network access and are never invoked by desktop inference.

History and opt-in feedback are unencrypted local storage. Feedback includes the pair and its prediction and is separate from training/evaluation data. Users should not treat this prototype as a hardened document vault. There is no telemetry, automatic updater, signing certificate, or remote service in this repository.

If you find a vulnerability, privately contact the maintainer of the GitHub repository distributing your copy rather than posting sensitive details or data in a public issue. Repository owners should enable GitHub private vulnerability reporting before public distribution.
