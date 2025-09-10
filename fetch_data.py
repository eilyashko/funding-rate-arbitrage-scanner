import datetime

import pandas as pd
from config import CONFIG
from exchange import init_exchange, get_all_trading_pairs, get_funding_rate, get_historical_funding_rates, get_ohlc
from utils import df_to_file, display_progress, build_run_directory


def fetch_and_save_data():
    """
    Fetches funding rates data from exchanges and saves it to files.

    This function iterates over the configured perpetual exchanges, fetches funding rates data
    for all perpetual trading pairs, retrieves current and historical rates, merges the dataframes,
    and saves them to files.
    """
    print(f"- Fetching data started")
    base_dir = build_run_directory(CONFIG['directory'])
    directory_data = f"{base_dir}/data"
    perp_exchanges = [init_exchange(exchange) for exchange in CONFIG['perpetual_exchanges']]
    spot_exchanges = []
    if CONFIG.get('get_spot_perp_opportunities'):
        spot_exchanges = [init_exchange(exchange) for exchange in CONFIG['spot_exchanges']]

    # Saving perpetual data
    for exchange in perp_exchanges:
        print(f"-- Fetching perpetual data for {exchange.name}")

        # Get all perpetual trading pairs
        perp_trading_pairs = get_all_trading_pairs(exchange, perpetual=True)
        if not perp_trading_pairs:
            continue
        print(f" {len(perp_trading_pairs)} perpetual trading pairs found")

        # Get current funding rates (optional)
        df_rates = pd.DataFrame({'pair': []})
        if CONFIG.get('fetch_current_rate', True):
            df_rates = get_funding_rates_for_pairs(exchange, perp_trading_pairs)

        # Get historical funding rates
        hours = CONFIG['funding_historical_days'] * 24
        df_historical_rates = get_historical_funding_rates_for_pairs(exchange, perp_trading_pairs, hours=hours)

        # Get daily amplitude data
        df_daily_amplitude = get_daily_amplitude(exchange, perp_trading_pairs)

        # Merge and save data to file
        base_df = df_rates if not df_rates.empty else pd.DataFrame({'pair': perp_trading_pairs})
        intersection_df = pd.merge(base_df, df_historical_rates, on='pair', how='left')
        intersection_df = pd.merge(intersection_df, df_daily_amplitude, on='pair', how='left')

        df_to_file(intersection_df, directory_data, f"funding_rates_{exchange.id}")

    # Saving spot data
    if CONFIG['get_spot_perp_opportunities']:
        for exchange in spot_exchanges:
            print(f"-- Fetching spot pairs for {exchange.name}")
            spot_pairs = get_spot_pairs(exchange)
            df_to_file(spot_pairs, directory_data, f"spot_pairs_{exchange.id}")

    print(f"- Fetching process finished. The data is saved in the directory: {directory_data}\n")


def get_funding_rates_for_pairs(exchange, trading_pairs):
    """
    Fetches current funding rates for specified trading pairs.

    Args:
        exchange (ccxt.Exchange): Exchange object.
        trading_pairs (list): List of trading pairs.

    Returns:
        pd.DataFrame: DataFrame containing current funding rates for each pair.
    """
    total_pairs = len(trading_pairs)
    data = []
    for index, pair in enumerate(trading_pairs):
        try:
            current_rate = get_funding_rate(exchange, pair)
            if current_rate is not None:
                data.append({'pair': pair, 'rate': current_rate})
        except Exception as e:
            print(f"Error fetching funding rate for {pair}: {e}")
            continue
        display_progress(index, total_pairs, info="Getting current funding rates")
    print("\r")
    return pd.DataFrame(data)


def get_historical_funding_rates_for_pairs(exchange, trading_pairs, hours=24):
    """
    Fetches historical funding rates for specified trading pairs.

    Args:
        exchange (ccxt.Exchange): Exchange object.
        trading_pairs (list): List of trading pairs.
        hours (int): Number of hours of historical data to fetch. Default is 24 hours.

    Returns:
        pd.DataFrame: DataFrame containing historical funding rates for each pair.
    """
    total_pairs = len(trading_pairs)
    data = []
    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    for index, pair in enumerate(trading_pairs):
        try:
            events = get_historical_funding_rates(exchange, pair, hours)
            if events:
                # Full window (e.g., 30d) is whatever we requested
                full_rates = [e['rate'] for e in events if 'rate' in e]

                # Derive 7d and 3d windows by timestamp filtering (no extra API calls)
                def rates_last_hours(window_hours):
                    cutoff = now_ms - window_hours * 60 * 60 * 1000
                    return [e['rate'] for e in events if e.get('timestamp') and e['timestamp'] >= cutoff]

                rates_7d = rates_last_hours(7 * 24)
                rates_3d = rates_last_hours(3 * 24)

                data.append({
                    'pair': pair,
                    'historical_rates': full_rates,
                    'historical_rates_7d': rates_7d,
                    'historical_rates_3d': rates_3d,
                })
        except Exception as e:
            print(f"Error fetching historical funding rate for {pair}: {e}")
            continue
        display_progress(index, total_pairs, info="Getting historical funding rates")
    print("\r")
    return pd.DataFrame(data)


def get_daily_amplitude(exchange, trading_pairs):
    """
    Fetches daily candle data of specified trading pairs and calculate mean and max amplitude.
    Amplitude is defined as high - low of a daily candle in percentage

    Args:
        exchange (ccxt.Exchange): Exchange object.
        trading_pairs (list): List of trading pairs.

    Returns:
        pd.DataFrame: DataFrame containing mean and max amplitude for each pair.
    """
    days = CONFIG['amplitude_days']
    current_time = int(datetime.datetime.now().timestamp() * 1000)
    start_time = current_time - days * 24 * 60 * 60 * 1000
    total_pairs = len(trading_pairs)
    data = []
    for index, pair in enumerate(trading_pairs):
        try:
            ohlc_data = get_ohlc(exchange, pair, start_date_ms=start_time, end_date_ms=current_time, timeframe='1d')
        except Exception as e:
            print(f"Error fetching ohlc data for {pair}: {e}")
            continue
        df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        df['amplitude'] = 100 * (df['high'] - df['low']) / df['open']

        mean_amplitude = round(df['amplitude'].mean(), 2)
        max_amplitude = round(df['amplitude'].max(), 2)
        amplitude_days = len(df)

        data.append({'pair': pair,
                     'mean_daily_amplitude': mean_amplitude,
                     'max_daily_amplitude': max_amplitude,
                     'amplitude_days': amplitude_days})

        display_progress(index, total_pairs, info="Getting daily amplitudes")
    print("\r")
    return pd.DataFrame(data)


def get_spot_pairs(exchange):
    """
    Fetches spot trading pairs from spot exchanges.

    Args:
        exchange (ccxt.Exchange): Exchange object.

    Returns:
        pd.DataFrame: DataFrame containing spot pairs.
    """
    try:
        spot_pairs = get_all_trading_pairs(exchange)
        return pd.DataFrame(spot_pairs, columns=['pair'])
    except Exception as e:
        print(f"Error fetching spot pairs for {exchange.name}: {e}")
        return pd.DataFrame(columns=['pair'])
