# ALGO DESCRIPTION
## Trading Algorithm Context (BTC/USD)
We have developed and validated a quantitative trading algorithm for the BTC/USD pair, optimized for intraday trading using 5-minute bars. The strategy has proven to be robust and consistently profitable in backtests covering various market regimes from 2020 to 2024.

### Key Strategy Components
Entry Filters
Primary Signal: Crossover of 9 and 20-period Exponential Moving Averages (EMAs) on the 5-minute timeframe.

Volume Confirmation: The volume of the signal candle must be at least 50% higher than the recent average.

Candle Filter: The signal candle must be a bullish/bearish candle with a body of at least 10% of its range.

Optional Filter (Hourly EMA): A 20-period EMA filter on the 1-hour timeframe can be enabled (ema_hourly_enable), although the most successful backtests (high CAGR) were achieved with this filter disabled.

### Risk Management and Exit
Dynamic Stop-Loss (Trailing Stop): A 2% trailing stop from the most favorable price reached.

Take-Profit: A 1% take-profit from the entry price.

Time-Based Exit: Position closure if SL/TP is not reached within 60 minutes.

Positions: Supports both long and short positions (enabled by the short_enable parameter).

Cost Simulation: Incorporates broker_fee_percentage (0.1%) and estimated_slippage_percentage (0.05%) modeled via a ConstantFeeModel. The native ConstantSlippageModel was disabled due to simulation errors.

Position Size: Configurable via the position_size_percent parameter (e.g., 0.99 for 99% of capital).

---

## Highlighted Results (Optimized Parameters)

| Metric | 2020 | 2021 | 2022 | 2023 | 2024 |
| :--------------- | :---------- | :---------- | :--------- | :---------- | :---------- |
| **CAGR** | 72.453% | 22.355% | 9.171% | 65.672% | 91.027% |
| **Drawdown** | 5.400% | 10.200% | 9.900% | 19.700% | 19.900% |
| **Sharpe Ratio** | 4.485 | 1.694 | 0.637 | 2.121 | 2.248 |
| **Total Orders** | 824 | 652 | 870 | 8572 | 9026 |
| **Win Rate** | 54% | 53% | 50% | 45% | 49% |
| **Profit-Loss Ratio** | 1.67 | 1.14 | 1.14 | 1.35 | 1.13 |
| **End Equity** | $1727.11 | $1223.55 | $1091.71 | $1656.72 | $1913.66 |

## Conclusion
The strategy has demonstrated a positive "edge" and great adaptability to different market conditions, proving highly profitable in trending markets and maintaining profitability in bearish markets. The next step is paper trading.

# BTC MVP Algorithm

QuantConnect algorithm implementing momentum trading strategy for BTC/USD with:
- EMA crossover signals
- Volume-filtered entries
- Multi-layered risk management
- Parameter-driven configuration

## Project Structure
```
.
├── algo/              # Core algorithm implementation
│   ├── main.py        # Primary trading logic
│   └── utilities/     # Helper functions and utilities
├── config/            # Configuration files
│   └── parameters.yml # Strategy parameters
├── scripts/           # Optimization and automation scripts
├── tests/             # Backtest scenarios and validation
└── docs/              # Strategy documentation
```

## Getting Started
1. Install QuantConnect Lean CLI
2. Configure credentials in `config/launch.json`
3. Run backtests:
```bash
lean backtest algo/main.py --parameters config/parameters.yml
```

## Key Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| fast_ema_period | 9 | Fast EMA window size |
| slow_ema_period | 20 | Slow EMA window size |
| stop_loss_percent | 0.5 | Maximum loss percentage per trade |
| take_profit_percent | 1 | Profit target percentage |
| broker_fee_percentage | 0.1 | Exchange commission rate |
| estimated_slippage_percentage | 0.05 | Expected price impact |
| volume_factor_percent | 50 | Minimum volume increase threshold |
| out_by_time_minutes | 60 | Maximum trade duration |
| trailing_stop_percent | 2 | Trailing stop percentage |
| hourly_ema_period | 20 | 1-hour EMA filter window |

## Optimization
```bash
python scripts/optimize.py --config config/parameters.yml
