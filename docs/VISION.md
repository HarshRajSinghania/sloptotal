# Vision

Longer-term direction, kept separate from [TODO.md](TODO.md) so the TODO
stays a list of concrete next steps. Nothing here is measured yet; anything
that ships goes through `tests/eval/` first, and anything that does not beat
the current engines on both corpora does not ship.

The aim is the VirusTotal model applied to AI-generated content: many
independent detectors, every vote visible, and published accuracy, across more
kinds of input than English prose.

## 1. Stronger statistical engines on bigger machines

Binoculars and Fast-DetectGPT currently use GPT-2-class models. On high-RAM CPU
servers or GPUs, larger open base models (Gemma, Qwen) could serve as
observer/performer pairs. The open question is whether the gain survives the
literary control corpus, since a stronger language model also finds classic
prose more predictable.

## 2. Specialised engines

Candidates worth measuring, each only as good as its numbers on both corpora:

| Area | Candidate | Why |
|---|---|---|
| Prompted LLM detectors | distil-labs/distil-ai-slop-detector-gemma | A different family from every engine we run today |
| Multilingual | tusarway/qwen3-0.6b-ai-detector | Small enough for CPU; needs a non-English corpus first |
| Fast screening | ModernBERT-based detectors (Vanguard, Earlybird) | Long context and low latency for the snippet path |

## 3. New kinds of input

**Source code.** Today's engines neither falsely accuse human code nor catch
machine-written code, so SlopTotal makes no claim about code. Doing better
would need different methods: code-trained language models for perplexity, and
structural features parsed with tree-sitter. It would also need a code corpus
with known provenance before any engine could be trusted.

**Other languages.** Most engines were trained on English. A multilingual
corpus with the same literary control (pre-LLM writing in each language) comes
before multilingual engines.
