# RATIO_REGNUM - Trading Edge Manifesto

## CORE PHILOSOPHY
We reject simplistic backtesting. We engineer systems that survive market realities.

## THE EDGE NARRATIVE
**Primary Insight**: BTC/ETH perpetual ratio mean-reverts during low-volatility regimes but trends during structural bull/bear markets. Without regime filtering, you're a gambler.

**Secondary Insight**: Funding rates on perpetuals destroy ratio strategies. A 0.01% 8h funding differential compounds to ~11% annually. We must trade only when funding is neutral.

**Execution Reality**: Limit orders fill 60% of the time in liquid markets. We simulate this, not fantasy perfect fills.

## ARCHITECTURAL PRINCIPLES
1. **No Future Leaks**: Event-driven, point-in-time data only
2. **Modularity**: Signal engine, risk manager, data layer are independent
3. **Realism First**: Slippage, partial fills, funding costs, exchange limits
4. **Diagnostic Intelligence**: Know WHY a trade worked, not just that it did

## REGIME FILTERING LOGIC
- **Trending Regime**: ADX(14) > 25 or expanding volatility → STAND ASIDE
- **Ranging Regime**: ADX < 25 and compressed volatility → ACTIVATE
- **Funding Regime**: |Funding_BTC - Funding_ETH| < 0.01% → ACTIVATE

## SUCCESS METRICS
- Sharpe Ratio > 1.5 over 2-year out-of-sample period
- Maximum drawdown < 15%
- Positive funding-adjusted returns
- Win rate > 55% with profit factor > 1.5