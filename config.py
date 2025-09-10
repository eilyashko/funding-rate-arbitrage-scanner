CONFIG = {
    'perpetual_exchanges': ['binance', 'gate'],
    # List of perpetual exchanges from which to obtain or analyze funding rates.
    # Specify exchange IDs according to the CCXT library format.
    # For a list of supported exchange IDs, refer to: https://docs.ccxt.com/#/?id=exchanges

    # 'spot_exchanges': ['binance', 'gate', 'htx', 'kucoin', 'bybit', 'okx'],
    # # List of spot exchanges for analyzing opportunities between Spot and Perpetual.
    # # Specify exchange IDs according to the CCXT library format.
    # # For a list of supported exchange IDs, refer to: https://docs.ccxt.com/#/?id=exchanges

    'fetch_and_save_data': True,
    # Whether the script should fetch funding rates from exchanges and save them to files
    # You can fetch the data first and then change this option to False and analyze the data

    'fetch_current_rate': False,
    # Whether to fetch current funding rates. If False, skips current rate requests for speed.

    'analyze_data_from_files': False,
    # Whether the script should analyze previously saved data from files.

    'directory': 'funding_data',
    # Base directory for storing data and results. Date-based subfolder used by default.

    'use_date_subfolder': True,
    # If True, create a date subfolder inside 'directory' (e.g., funding_data/20240910/...)

    'date_subfolder_format': '%Y%m%d',
    # Date format for the date subfolder when 'use_date_subfolder' is True.
    # For example: '%Y%m%d' -> 20240910, '%Y-%m-%d' -> 2024-09-10

    'date_subfolder': '',
    # Optional manual date string to use instead of today. Leave empty to use current date.

    'file_format': 'xlsx',
    # The file format for saving and importing files. Define 'csv' or 'xlsx'

    'funding_historical_days': 30,
    # Number of days for historical funding rates that used for calculating average daily rate

    'amplitude_days': 30,
    # Number of days for calculating average and maximum daily amplitude, representing asset volatility.
    # Amplitude is the percentage difference between the daily high and low, relative to the opening price.
    # Higher amplitudes indicate greater asset volatility.

    'funding_rate_threshold': 0.01,
    # Minimum funding rate (or rate difference). Data below this threshold will be filtered out

    'get_spot_perp_opportunities': False,
    # Whether to analyze opportunities between Spot and Perpetual markets

    'get_perp_perp_opportunities': True
    # Whether to analyze opportunities within Perpetual markets
}
