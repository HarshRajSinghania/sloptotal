# TODO

Concrete next steps. Longer-range ideas are in [docs/VISION.md](VISION.md).

## Engines

- [ ] **Add Gradient** (`ShantanuT01/gradient-ai-text-detector`, MIT): RAID AUC
  0.998 without RAID training, literary bias 0.033. Load as float32, re-derive
  `ENGINE_WEIGHTS` on both corpora, report before/after. See
  [tests/eval/FINDINGS.md](../tests/eval/FINDINGS.md#newer-open-detectors-measured-standalone).
- [ ] Evaluate **Earlybird-fast** (84 ms/text) for the snippet path.
- [ ] Build an out-of-distribution corpus (not RAID) so RAID-trained models
  (TMR, tabularisai, GeorgeDrayson) can be judged fairly.
- [ ] Harness for prompted LLM detectors (distil-labs Gemma slop detector).
- [ ] Qwen / Gemma base models as Binoculars-style observer/performer pairs on
  high-RAM CPU servers.

## Site check

- [ ] More builders once their markers are verified (see
  [docs/SITE_FINGERPRINTS.md](SITE_FINGERPRINTS.md)).
- [ ] Render JavaScript-only pages (optional headless browser) so the copy of
  AI-builder sites can be scored.

## Infrastructure

- [ ] `/health` reports engines that loaded, not only engines registered.
- [ ] Publish per-engine RAM and latency in `docs/MODELS.md`.
