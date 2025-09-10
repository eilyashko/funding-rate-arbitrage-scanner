CURRENT_RATES_CONFIG = {
    'perpetual_exchanges': ['binance', 'gate'],
    # Limited list for ad-hoc current-rate fetches

    'directory': 'funding_data',
    # Files are saved under funding_data/<date>/data by default (global CONFIG)

    # Optional filter for pairs to speed things up. If None or empty, fetch all perpetual pairs.
    # Example: ['BTC/USDT:USDT', 'ETH/USDT:USDT']
    'pairs_filter': [],
}


