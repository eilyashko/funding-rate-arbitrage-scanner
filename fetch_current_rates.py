import pandas as pd
from typing import List

from exchange import init_exchange, get_all_trading_pairs, get_funding_rate
from utils import df_to_file, display_progress, build_run_directory


def fetch_current_rates(exchanges: List[str], directory: str,
                        pairs_filter: List[str] | None = None) -> None:
    """
    Fetch current funding rates for selected exchanges, optionally filtered by pairs.

    Args:
        exchanges (List[str]): Exchange ids to fetch from.
        directory (str): Root directory to save files.
        pairs_filter (List[str] | None): If provided, only these pairs are requested.
    """
    base_dir = build_run_directory(directory)
    target_dir = f"{base_dir}/data"

    for exchange_id in exchanges:
        exchange = init_exchange(exchange_id)
        print(f"-- Fetching current rates for {exchange.name}")

        if pairs_filter:
            perp_pairs = pairs_filter
        else:
            perp_pairs = get_all_trading_pairs(exchange, perpetual=True)
        if not perp_pairs:
            print(f"No perpetual pairs found for {exchange_id}")
            continue

        total_pairs = len(perp_pairs)
        data = []
        for index, pair in enumerate(perp_pairs):
            try:
                current_rate = get_funding_rate(exchange, pair)
                if current_rate is not None:
                    data.append({'pair': pair, 'rate': current_rate})
            except Exception as e:
                print(f"Error fetching funding rate for {pair} on {exchange_id}: {e}")
                continue
            display_progress(index, total_pairs, info="Getting current funding rates")
        print("\r")

        df = pd.DataFrame(data)
        df_to_file(df, target_dir, f"funding_rates_{exchange.id}")


if __name__ == "__main__":
    # Minimal inline config for ad-hoc requests. Adjust as needed.
    from config_current_rates import CURRENT_RATES_CONFIG

    fetch_current_rates(
        exchanges=CURRENT_RATES_CONFIG['perpetual_exchanges'],
        directory=CURRENT_RATES_CONFIG['directory'],
        pairs_filter=CURRENT_RATES_CONFIG.get('pairs_filter')
    )


