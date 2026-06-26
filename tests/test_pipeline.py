# tests/test_pipeline.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

''''''
from orchestrator.master_orchestrator import MasterOrchestrator

# Test with multiple symbols
symbols = ["AAPL", "TSLA", "MSFT"]

orchestrator = MasterOrchestrator()

for symbol in symbols:
    print(f"\n{'='*50}")
    print(f"  ANALYZING: {symbol}")
    print(f"{'='*50}")

    report = orchestrator.analyze(symbol)

    print(f"  Decision   : {report.final_decision}")
    print(f"  Confidence : {report.confidence}%")
    print(f"  Duration   : {report.duration_ms}ms")
    print(f"  Scores     : {report.scores}")
    print(f"  Errors     : {report.errors}")
''''''
from agents.market_data_agent import MarketDataAgent
from agents.technical_analysis_agent import TechnicalAnalysisAgent
# ... rest of file stays the same
# tests/test_pipeline.py

from agents.market_data_agent import MarketDataAgent
from agents.technical_analysis_agent import TechnicalAnalysisAgent

# --- Agent 1: Fetch Data ---
market_agent = MarketDataAgent()
market_result = market_agent.run("AAPL")

print("=== MARKET DATA RESULT ===")
print("Success:", market_result.success)
print("Score:", market_result.score)
print("Close:", market_result.data["snapshot"]["close"])
print()

# --- Agent 4: Technical Analysis ---
tech_agent = TechnicalAnalysisAgent()
tech_result = tech_agent.run(
    "AAPL",
    price_history=market_result.data["price_history"]
)

print("=== TECHNICAL ANALYSIS RESULT ===")
print("Score:", tech_result.score)
print()
print("Signal Summary:")
print("  Bullish:", tech_result.data["signals"]["bullish"])
print("  Bearish:", tech_result.data["signals"]["bearish"])
print("  Neutral:", tech_result.data["signals"]["neutral"])
print()
print("Individual Signals:")
for name, detail in tech_result.data["signals"]["details"].items():
    signal = detail["signal"]
    value  = detail["value"]
    print(f"  {name:<15} {signal:<20} {value}")
print()
print("Key Indicators:")
ind = tech_result.data["indicators"]
print(f"  RSI   : {ind['rsi']}")
print(f"  MACD  : {ind['macd']}")
print(f"  EMA20 : {ind['ema20']}")
print(f"  ADX   : {ind['adx']}")