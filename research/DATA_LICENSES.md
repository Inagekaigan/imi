# Data and model provenance

Imi-authored code and materials have no public reuse license; see LICENSE. Dependencies, corpora and pretrained models retain their own licenses.

## MTPEdocs-MQM

Source: https://github.com/tr4lg/MTPEdocs-MQM at commit `f2a25fb0e8e729c3e32505ae33ea5a9121ae69fe`.
Downloaded files and checksums are recorded in `data/mtpedocs-manifest.json`. Retain upstream attribution when using the annotations.

The upstream repository licenses its annotations under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0**, explicitly excluding the source documents. We use published Japanese-English TexTra and Google outputs and their human MQM annotations for a local research pilot. We do not claim that the upstream license grants commercial rights to the source text or automatically settles the legal status of derived model weights.

Raw and processed natural text are excluded from Git and the source archive. Reproduction downloads directly from the attributed source. The local checkpoint is research-only pending a redistribution and source-rights review. The project notice does not grant redistribution rights for the bundled neural binary or checkpoint. A code-only release can be published independently. The desktop's research-use notice is deliberate.

## Authored contrastive examples

`contrastive.py` contains Imi-authored examples with no public reuse license granted (see LICENSE). They are generated constructions, not collected human judgments. They include positive and negative translations, scopes, modalities, quantities, agents and deadlines. No independent Japanese expert has verified these labels. Count them separately from natural MT.

## Pretrained encoder

FacebookAI/XLM-RoBERTa-base, revision `e73636d4f797dec63c3081bb6ed5c7b0bb3f2089`, upstream model license MIT. https://huggingface.co/FacebookAI/xlm-roberta-base . The local original weight SHA-256 is `6fd4797bc397c3b8b55d6bb5740366b57e6a3ce91c04c77f22aafc0c128e6feb`.

## Typography and runtimes

IBM Plex Sans and Newsreader fonts are bundled with their SIL Open Font License notices under `src/assets/fonts/`. Electron, Python, PyTorch, ONNX Runtime, tokenizers and their dependencies retain their respective upstream licenses. The packaged runtime retains dependency files and notices. This project's license does not replace those licenses.
