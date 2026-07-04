# tests/test_regime.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.market_data_agent import MarketDataAgent
from agents.regime_agent import RegimeDetectionAgent

m = MarketDataAgent()
market = m.run("AAPL")

r = RegimeDetectionAgent()
result = r.run("AAPL", price_history=market.data["price_history"])

print("Regime    :", result.data["regime"])
print("Confidence:", result.data["confidence"])
print("Score     :", result.score)
print()
print("Key Indicators:")
ind = result.data["indicators"]
print(f"  Return 5d  : {ind['return_5d']}%")
print(f"  Return 20d : {ind['return_20d']}%")
print(f"  Return 50d : {ind['return_50d']}%")
print(f"  Vol 20d    : {ind['volatility_20d']}%")
print(f"  Vol ratio  : {ind['vol_ratio']}")
print(f"  Above SMA20: {ind['above_sma20']}")
print(f"  Above SMA50: {ind['above_sma50']}")