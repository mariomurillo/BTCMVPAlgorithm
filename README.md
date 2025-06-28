# ALGO DESCRIPTION
{% RESULTS.md %}

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
