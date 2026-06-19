# Stage-B — QAOA on a real Nifty-100 sector QUBO (quantum showcase)

Real instance: **8 sector buckets** (equal-weight Nifty-100 constituents), cardinality k=3. `gap` = solver energy − exact optimum (0 = optimal).

| solver | energy | gap | time |
|---|---|---|---|
| exact (2ⁿ) | -0.5903 | 0.0000 | 1 ms |
| simulated annealing | -0.5903 | +0.0000 | 820 ms |
| **QAOA** (p=2) | -0.5903 | +0.0000 | 54.1 s |

**QAOA reproduced the exact optimum** on this real instance. Exact selection (k=3): ['INFRA', 'PHARMA', 'CONSUMER'].

## The scaling wall (why this is sector-reduced, not the full 100)

- QAOA on a statevector simulator needs **2ⁿ amplitudes**; the full Nifty-100 QUBO is n=100 → 2¹⁰⁰, impossible. The synthetic benchmark already measured the wall at n=10 (~12 min, gap +0.20). NISQ hardware can't do 100 clean qubits at depth either.
- So the **quantum solver is a method demonstration on a reduced real instance**; the full 100-asset selection is solved classically (simulated annealing) in `exp_qubo_universe.py`.
- Honest scope: this validates the **solver**, not portfolio returns (see `reports/qubo_universe_findings.md` for the return question — QUBO selection does not beat the survivorship-inflated 1/N net of tax).
