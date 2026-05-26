from __future__ import annotations

import argparse

from smart_system_a import SmartSystemAAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smart System A XAUUSD analysis agent.")
    parser.add_argument("--h4", required=True, help="Path to H4 OHLCV CSV.")
    parser.add_argument("--h1", required=True, help="Path to H1 OHLCV CSV.")
    parser.add_argument("--balance", type=float, required=True, help="Account balance.")
    parser.add_argument("--risk-mode", choices=["standard", "high_confidence"], default="standard")
    parser.add_argument("--risk-percent", type=float, default=None)
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--volume-override", action="store_true", help="Explicitly allow condition 6 override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    agent = SmartSystemAAgent()
    result = agent.analyze_csv(
        h4_path=args.h4,
        h1_path=args.h1,
        balance=args.balance,
        risk_mode=args.risk_mode,
        symbol=args.symbol,
        risk_percent=args.risk_percent,
        volume_override=args.volume_override,
    )
    print(agent.format_result(result))


if __name__ == "__main__":
    main()
