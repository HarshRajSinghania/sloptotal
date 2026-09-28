# Benchmarks

Speed, load and older accuracy scripts. They talk to a running instance
(`http://localhost:8000` by default, `SLOPTOTAL_URL` where supported) and write
their reports to `benchmarks/results/`. Run them from the repository root.

| Script | Measures |
|---|---|
| `bench_engines.py`, `bench_full.py`, `bench_realistic.py` | Per-engine latency and snippet accuracy, in-process |
| `bench_snippets.py` | Snippet-scan throughput, the browser-extension workload |
| `load_test.py` | CLI load generator (`--url`, `--concurrency`) |
| `concurrency_test.py`, `realistic_load_test.py` | Queue behaviour under concurrent and realistic mixed traffic |
| `eval_dataset.py`, `eval_hard.py`, `eval_urls.py`, `eval_diagnose.py` | Early accuracy runs on RAID and MAGE samples |

The accuracy numbers quoted in the README come from the newer, reproducible
harness in [`tests/eval/`](../tests/eval/), not from these scripts.
