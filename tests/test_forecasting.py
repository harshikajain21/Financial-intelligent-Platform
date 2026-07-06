# tests/test_forecasting.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.market_data_agent import MarketDataAgent
from agents.forecasting_agent import ForecastingAgent

print("Fetching market data...")
market = MarketDataAgent()
m = market.run("AAPL")
print(f"Got {m.data['bars_fetched']} bars of data")
print()

print("Running forecasting models (Prophet takes ~30 seconds on first run)...")
forecaster = ForecastingAgent()
result = forecaster.run("AAPL", price_history=m.data["price_history"])

print()
print("=== FORECASTING RESULTS ===")
print(f"Score        : {result.score}")
print(f"Models used  : {result.data['models_used']}")
print(f"Current Price: ${result.data['current_price']:.2f}")
print()
print("Predictions:")
for horizon, data in result.data["forecasts"].items():
    direction = "UP" if data["change_pct"] >= 0 else "DOWN"
    print(f"  {horizon:5} -> ${data['price']:.2f}  ({data['change_pct']:+.2f}%)  [{direction}]")
    print(f"         Range: ${data['lower']:.2f} - ${data['upper']:.2f}")