# tests/test_anomaly.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.market_data_agent import MarketDataAgent
from agents.anomaly_agent import AnomalyDetectionAgent

m = MarketDataAgent()
market = m.run("AAPL")

a = AnomalyDetectionAgent()
result = a.run("AAPL", price_history=market.data["price_history"])

print("Score          :", result.score)
print("Anomaly Count  :", result.data["anomaly_count"])
print("Severity Score :", result.data["severity_score"])
print()
if result.data["anomalies"]:
    print("Anomalies Detected:")
    for anomaly in result.data["anomalies"]:
        print(f"  [{anomaly['severity']}] {anomaly['type']} | {anomaly['detail']} | {anomaly['date']}")
else:
    print("No anomalies detected — clean trading activity.")