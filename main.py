"""
main.py — Financial Intelligence Platform entry point.

Usage:
    # Start the FastAPI server
    python main.py serve

    # Run a quick CLI analysis
    python main.py analyse --tickers AAPL MSFT --start 2023-01-01 --end 2024-01-01

    # Run a backtest
    python main.py backtest --ticker AAPL --strategy sma_crossover --start 2020-01-01 --end 2024-01-01
"""

from __future__ import annotations

import argparse
import json
import sys


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the FastAPI / Uvicorn server."""
    import uvicorn

    from config.settings import Settings
    s = Settings()
    print(f"Starting {s.app_name} on {s.api_host}:{s.api_port}")
    uvicorn.run(
        "api.main:app",
        host=s.api_host,
        port=s.api_port,
        reload=args.reload,
        log_level=s.log_level.lower(),
    )


def cmd_analyse(args: argparse.Namespace) -> None:
    """Run a full analysis from the command line."""
    from orchestrator.master_orchestrator import MasterOrchestrator

    orchestrator = MasterOrchestrator()
    print(f"Analysing {args.tickers} from {args.start} to {args.end}…")
    result = orchestrator.analyse(
        tickers=args.tickers,
        start=args.start,
        end=args.end,
        interval=args.interval,
    )

    # Print fusion recommendations
    fusion = result.get("fusion", {})
    print("\n── Recommendations ──────────────────────────────────────")
    for ticker, rec in fusion.items():
        print(
            f"  {ticker:10s}  {rec['recommendation']:15s}  "
            f"confidence={rec['confidence']:.1%}  "
            f"score={rec['composite_score']:.4f}"
        )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nFull result written to {args.output}")


def cmd_backtest(args: argparse.Namespace) -> None:
    """Run a backtest from the command line."""
    from backtesting.engine import BacktestEngine

    engine = BacktestEngine()
    print(f"Backtesting {args.ticker} with {args.strategy} [{args.start} → {args.end}]…")
    result = engine.run(
        ticker=args.ticker,
        strategy_name=args.strategy,
        start=args.start,
        end=args.end,
        initial_capital=args.capital,
    )

    m = result["metrics"]
    print("\n── Backtest Results ─────────────────────────────────────")
    print(f"  Total Return:       {m['total_return_pct']:.2f}%")
    print(f"  Annualised Return:  {m['annualised_return_pct']:.2f}%")
    print(f"  Sharpe Ratio:       {m['sharpe_ratio']:.3f}")
    print(f"  Max Drawdown:       {m['max_drawdown_pct']:.2f}%")
    print(f"  Final Capital:      ${result['final_capital']:,.2f}")
    print(f"  Number of Trades:   {len(result['trades'])}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Financial Intelligence Platform CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # serve
    serve_p = subparsers.add_parser("serve", help="Start the API server")
    serve_p.add_argument("--reload", action="store_true", help="Enable hot-reload (dev)")
    serve_p.set_defaults(func=cmd_serve)

    # analyse
    analyse_p = subparsers.add_parser("analyse", help="Run full financial analysis")
    analyse_p.add_argument("--tickers", nargs="+", required=True, metavar="TICKER")
    analyse_p.add_argument("--start", required=True, metavar="YYYY-MM-DD")
    analyse_p.add_argument("--end", required=True, metavar="YYYY-MM-DD")
    analyse_p.add_argument("--interval", default="1d", choices=["1d", "1wk", "1mo"])
    analyse_p.add_argument("--output", metavar="FILE", help="Write full JSON result to file")
    analyse_p.set_defaults(func=cmd_analyse)

    # backtest
    backtest_p = subparsers.add_parser("backtest", help="Run a strategy backtest")
    backtest_p.add_argument("--ticker", required=True)
    backtest_p.add_argument(
        "--strategy", required=True,
        choices=["buy_and_hold", "sma_crossover", "rsi_mean_revert", "macd_signal"],
    )
    backtest_p.add_argument("--start", required=True, metavar="YYYY-MM-DD")
    backtest_p.add_argument("--end", required=True, metavar="YYYY-MM-DD")
    backtest_p.add_argument("--capital", type=float, default=100_000.0, metavar="AMOUNT")
    backtest_p.set_defaults(func=cmd_backtest)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
