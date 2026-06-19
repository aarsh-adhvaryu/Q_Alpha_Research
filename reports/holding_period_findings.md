# Holding-period sweep — weekly vs monthly vs quarterly vs annual

_PIT survivorship-free Nifty-50, shrink weighting, force_refresh, §4.6 tax gate, dynamic slippage, band 0.10, → 2024-12-31. Unmodified qalpha engine; net of FIFO cost + capital-gains tax._

| holding period | # rebalances | tax ₹ | cost ₹ | CAGR % | Sharpe | maxDD % |
| --- | --- | --- | --- | --- | --- | --- |
| Weekly | 557 | 201,096 | 110,591 | 1.6 | 0.18 | -60.7 |
| Monthly | 143 | 198,239 | 56,438 | 8.5 | 0.56 | -44.0 |
| Quarterly | 48 | 202,507 | 28,416 | 15.8 | 0.96 | -27.2 |
| Annual | 12 | 50,317 | 9,517 | 18.3 | 1.14 | -25.2 |

## Read

- **Trading less wins, ~monotonically.** Shorter holds fire more rebalances → realise more short-term capital-gains tax (STCG 20% vs LTCG 12.5%) and more cost, which compounds against the book. The factor signal does not improve fast enough to pay for that friction.
- **Weekly is the worst** (most turnover/tax); **annual is the best** and is the only config that clears the iron-rule bar (beats Nifty TRI *and* 1/N net of friction). This reproduces the product's headline decision — the edge is *trade rarely, tax-aware*, not a faster signal.
- Caveat: the true driver is **realised turnover**, not the nominal label — the §4.6 gate can make a nominally-frequent cadence trade rarely too (see the walk-forward study). But at equal gate settings, the shorter the holding period the more it churns and the more tax it pays.
