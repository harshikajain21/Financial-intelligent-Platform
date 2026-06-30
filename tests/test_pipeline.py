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