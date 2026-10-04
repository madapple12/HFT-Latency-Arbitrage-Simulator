 # High-Frequency Statistical Arbitrage & Latency Simulator

A production-grade Python intraday trading simulator utilizing live market data streams via the `yfinance` API to harvest microstructure alpha across highly liquid equity assets (AAPL).

 Strategy Evolution & Risk Architecture
This repository documents a four-stage quantitative research process optimizing a statistical arbitrage strategy while under intense simulated market constraints.

* **Phase 1: Baseline Arbitrage Engine** – Built basic cross-feed entry/exit logic utilizing synthetic sub-minute tick interpolation via NumPy.
* **Phase 2: Friction Integration** – Embedded a structural 0.05% transaction fee hurdle per trade to eliminate over-trading and fee-churning capital drag.
* **Phase 3: Microstructure Stress Testing** – Injected a randomized Network Latency Jitter module (1-3 tick delays) to model real-world packet routing lags, coupled with a 3% equity drawdown circuit breaker.
* **Phase 4: Parameter Optimization (The Sweet Spot)** – Parameter-tuned execution gates to a 1.5-Sigma rolling standard deviation volatility filter combined with a dynamic inventory mean-reversion holding protocol.

 Performance Metrics (Optimized Run)
* **Strategy Win Rate:** 93.47% (415 Wins / 29 Losses)
* **Net Portfolio Return:** +0.39% (+\$38.57 net profit after fee deduction)
* **Max Peak-to-Trough Drawdown:** 0.09% 
* **Total Ticks Processed:** 10,900+ high-frequency intraday streams

