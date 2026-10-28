# Contributing

Run `npm ci`, `npm test`, and `npm run smoke` before submitting a change. Rebuild with `npm run dist` after changing packaged source or model files.

For an NLP change, add a failing contrastive example and an aligned control, explain the affected language pattern, and document limits. Do not fix one example by silently widening claims of coverage. Keep synthetic benchmarks labeled synthetic and never tune to an independently reserved real test set.

`npm run train` retrains only the original cue-feature baseline. Neural changes use the separate `research/` training and evaluation pipeline described in README.md. Preserve baseline comparisons. Never overwrite the published final evaluation after tuning against its failures; reserve new data for the next experiment. Changes to the feature layout require a schema-version migration.

Natural corpus text and research weights are excluded from Git. Follow research/DATA_LICENSES.md; do not apply the code's MIT license to the corpus or derived checkpoint. Annotator agreement, external baseline runs and clean-machine tests must be labeled pending until performed.

Avoid remote scripts, telemetry, raw renderer access to Node.js or IPC, and implicit exports of user text. Do not commit credentials, private corpora, personal history, node_modules, or release binaries. The workflow uploads build artifacts rather than pushing them to the source repository.
