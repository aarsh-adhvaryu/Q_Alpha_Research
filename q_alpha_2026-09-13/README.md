# research/ from Q_Alpha, moved here on 2026-09-13

Q_Alpha became an AI investor and now keeps only the code that system runs. Its `research/` folder —
ideas that never passed a pre-registered test (QUBO/QAOA, LPPLS, the HMM risk-state overlay, options
and hedge readouts, an exposure overlay) — was moved here unchanged, so it keeps running.

- `research/` — copied as it was in Q_Alpha at commit `9788f60`.
- `src/qalpha/` — only the 24 Q_Alpha modules `research/` imports (the old optimizer: factors,
  alloc, backtest engine; the accounting engine; the futures hedge), copied at the same commit. The
  package `__init__.py` files are bare markers; the originals imported the live broker layer.

## Run the tests

From this folder, with a Python environment that has Q_Alpha's dependencies plus `hmmlearn`
(and `qiskit`, `qiskit-algorithms`, `qiskit-optimization` for the quantum tests, which skip without them):

```bash
PYTHONPATH="src:." python -m pytest research/tests -q
```

On 2026-09-13 this gave **13 passed, 2 skipped** — identical to the same suite inside Q_Alpha.

`src/qalpha/` must come first on the path: an installed Q_Alpha would otherwise shadow it, and
Q_Alpha no longer contains these modules.
