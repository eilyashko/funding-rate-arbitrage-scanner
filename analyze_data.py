import re

import pandas as pd
from itertools import combinations
import ast
from config import CONFIG
from utils import df_to_file, file_to_df, build_run_directory


def analyze_data():
    """
    Analyzes funding rates data from files and identifies trading opportunities.

    This function reads funding rates data from files, creates dataframes for each exchange,
    and identifies trading opportunities between perpetual contracts (Perpetual-Perpetual) and
    between perpetual contracts and spot markets (Spot-Perpetual).
    """
    base_dir = build_run_directory(CONFIG['directory'])
    directory_data = f"{base_dir}/data"
    directory_result = f"{base_dir}/result"
    perpetual_exchanges_str = '_'.join(CONFIG['perpetual_exchanges'])

    # Load perpetual data from files
    perpetual_data_df = create_perpetual_data_df_from_files(directory_data)
    if not perpetual_data_df:
        return

    print(f"- Analyzing Funding rates from files")

    # Analyze Perpetual-Perpetual opportunities
    if CONFIG['get_perp_perp_opportunities']:
        print(f"-- Analyzing Perpetual-Perpetual opportunities")
        if len(perpetual_data_df) < 2:
            print(f"Warning: Skip Perpetual-Perpetual opportunities analysis. More than 2 perpetual exchanges needed.")
        else:
            perp_exchange_combinations = list(combinations(perpetual_data_df.keys(), 2))
            final_df = pd.DataFrame()
            for combination in perp_exchange_combinations:
                exchange_1, exchange_2 = combination[0], combination[1]
                df_1, df_2 = perpetual_data_df[exchange_1], perpetual_data_df[exchange_2]

                df = create_perp_perp_opportunities_df(exchange_1, exchange_2, df_1, df_2)
                final_df = pd.concat([final_df, df], ignore_index=True)

            if not final_df.empty:
                main_days = CONFIG['funding_historical_days']
                diff_col = f"cumulative_rate_diff_{main_days}d"
                sort_by = diff_col if diff_col in final_df.columns else 'APY_historical_average'
                final_df = final_df.sort_values(by=sort_by, ascending=False, ignore_index=True)

                df_to_file(final_df, directory_result, f"result_perp_perp_{perpetual_exchanges_str}")
                print(f"-- Analysis process finished. The data is saved in the directory: {directory_result}")

    # Analyze Spot-Perpetual opportunities
    if CONFIG['get_spot_perp_opportunities']:
        print(f"-- Analyzing Spot-Perpetual opportunities")

        spot_pairs_df = create_spot_data_df_from_files(directory_data)
        if spot_pairs_df.empty:
            return

        final_df = pd.DataFrame()
        for perpetual_exchange, perpetual_rates_df in perpetual_data_df.items():
            df = create_spot_perp_opportunites_df(perpetual_exchange, perpetual_rates_df, spot_pairs_df)
            final_df = pd.concat([final_df, df], ignore_index=True)
        positive_rates_df = filter_and_sort_rates(final_df, negative=False)
        negative_rates_df = filter_and_sort_rates(final_df, negative=True)

        df_to_file(positive_rates_df, directory_result, f"result_spot_perp_positive_{perpetual_exchanges_str}")
        df_to_file(negative_rates_df, directory_result, f"result_spot_perp_negative_{perpetual_exchanges_str}")
        print(f"-- Analysis process finished. The data is saved in the directory: {directory_result}")


def create_perpetual_data_df_from_files(directory_data):
    """
    Creates a dictionary of perpetual data dataframes from files.

    Args:
        directory_data (str): Directory containing files.

    Returns:
        dict: Dictionary with exchange names as keys and dataframes as values.
    """
    perpetual_data = {}
    for exchange in CONFIG['perpetual_exchanges']:
        df = file_to_df(f"{directory_data}", f"funding_rates_{exchange}")
        if not df.empty:
            df['pair'] = df['pair'].apply(remove_leading_numbers)
            perpetual_data[exchange] = df
    if len(perpetual_data) == 0:
        print(f"- Exiting: Perpetual exchange data not found.")
        return False
    print(f"Data for perpetual exchanges ({', '.join(perpetual_data.keys())}) loaded successfully")

    return perpetual_data


def create_spot_data_df_from_files(directory_data):
    """
    Creates a dataframe of spot trading pairs from files.

    Args:
        directory_data (str): Directory containing files.

    Returns:
        pd.DataFrame: DataFrame containing trading pairs and the exchanges where each pair is available.
    """
    spot_data = []
    for exchange in CONFIG['spot_exchanges']:
        df = file_to_df(f"{directory_data}", f"spot_pairs_{exchange}")
        if not df.empty:
            df['spot_exchange'] = exchange
            spot_data.append(df)
    if len(spot_data) == 0:
        print("- Exiting: No spot data found")
        return pd.DataFrame()
    combined_df = pd.concat(spot_data).groupby('pair')['spot_exchange'].apply('/'.join).reset_index()
    return combined_df


def create_perp_perp_opportunities_df(exchange_1, exchange_2, df_1, df_2):
    """
    Creates a dataframe of Perpetual-Perpetual trading opportunities.

    Args:
        exchange_1 (str): Name of the first exchange.
        exchange_2 (str): Name of the second exchange.
        df_1 (pd.DataFrame): Dataframe of funding rates for exchange_1.
        df_2 (pd.DataFrame): Dataframe of funding rates for exchange_2.

    Returns:
        pd.DataFrame: DataFrame containing Perpetual-Perpetual trading opportunities.
    """
    df = pd.merge(df_1, df_2, on='pair', how='inner')

    # Helper: coerce historical rates to list regardless of source type (str/list/NaN)
    def coerce_to_list(value):
        if isinstance(value, list):
            return value
        if pd.isna(value):
            return []
        if isinstance(value, str):
            try:
                parsed = ast.literal_eval(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        return []

    # Ensure auxiliary 7d/3d columns exist
    if 'historical_rates_7d_x' not in df.columns:
        df['historical_rates_7d_x'] = [[] for _ in range(len(df))]
    if 'historical_rates_7d_y' not in df.columns:
        df['historical_rates_7d_y'] = [[] for _ in range(len(df))]
    if 'historical_rates_3d_x' not in df.columns:
        df['historical_rates_3d_x'] = [[] for _ in range(len(df))]
    if 'historical_rates_3d_y' not in df.columns:
        df['historical_rates_3d_y'] = [[] for _ in range(len(df))]

    # Identify historical rates for short and long exchanges (safe)
    df['historical_rates_x'] = df['historical_rates_x'].apply(coerce_to_list)
    df['historical_rates_y'] = df['historical_rates_y'].apply(coerce_to_list)
    df['historical_rates_7d_x'] = df['historical_rates_7d_x'].apply(coerce_to_list)
    df['historical_rates_7d_y'] = df['historical_rates_7d_y'].apply(coerce_to_list)
    df['historical_rates_3d_x'] = df['historical_rates_3d_x'].apply(coerce_to_list)
    df['historical_rates_3d_y'] = df['historical_rates_3d_y'].apply(coerce_to_list)

    # Compute cumulative sums first, independent of current rates
    df['sum_x'] = df['historical_rates_x'].apply(sum)
    df['sum_y'] = df['historical_rates_y'].apply(sum)
    df['cumulative_rate_diff'] = df['sum_x'] - df['sum_y']
    df['APY_historical_average'] = 365 * df['cumulative_rate_diff'] / CONFIG['funding_historical_days']
    df['APY_historical_average'] = df['APY_historical_average'].round(decimals=2)

    # Determine short/long exchanges: prefer current rates if available, else by cumulative difference
    has_current = ('rate_x' in df.columns and 'rate_y' in df.columns)
    if has_current:
        df['short_exchange'] = exchange_1
        df['long_exchange'] = exchange_2
        df.loc[df['rate_x'] < df['rate_y'], ['short_exchange', 'long_exchange']] = exchange_2, exchange_1
        df['short_rate'] = df.apply(lambda x: x['rate_x'] if x['short_exchange'] == exchange_1 else x['rate_y'], axis=1)
        df['long_rate'] = df.apply(lambda x: x['rate_x'] if x['long_exchange'] == exchange_1 else x['rate_y'], axis=1)
        df['rate_diff'] = df['short_rate'] - df['long_rate']
    else:
        df['short_exchange'] = df.apply(lambda x: exchange_1 if x['cumulative_rate_diff'] > 0 else exchange_2, axis=1)
        df['long_exchange'] = df.apply(lambda x: exchange_2 if x['cumulative_rate_diff'] > 0 else exchange_1, axis=1)

    df['short_historical_rates'] = df.apply(
        lambda x: x['historical_rates_x'] if x['short_exchange'] == exchange_1
        else x['historical_rates_y'], axis=1)
    df['long_historical_rates'] = df.apply(
        lambda x: x['historical_rates_x'] if x['long_exchange'] == exchange_1
        else x['historical_rates_y'], axis=1)

    # 7d/3d aligned to short/long
    df['short_historical_rates_7d'] = df.apply(
        lambda x: x['historical_rates_7d_x'] if x['short_exchange'] == exchange_1
        else x['historical_rates_7d_y'], axis=1)
    df['long_historical_rates_7d'] = df.apply(
        lambda x: x['historical_rates_7d_x'] if x['long_exchange'] == exchange_1
        else x['historical_rates_7d_y'], axis=1)
    df['short_historical_rates_3d'] = df.apply(
        lambda x: x['historical_rates_3d_x'] if x['short_exchange'] == exchange_1
        else x['historical_rates_3d_y'], axis=1)
    df['long_historical_rates_3d'] = df.apply(
        lambda x: x['historical_rates_3d_x'] if x['long_exchange'] == exchange_1
        else x['historical_rates_3d_y'], axis=1)

    # Calculate cumulative rates per side
    df['short_cumulative_rate'] = df['short_historical_rates'].apply(sum)
    df['long_cumulative_rate'] = df['long_historical_rates'].apply(sum)
    df['short_cumulative_rate_7d'] = df['short_historical_rates_7d'].apply(sum)
    df['long_cumulative_rate_7d'] = df['long_historical_rates_7d'].apply(sum)
    df['short_cumulative_rate_3d'] = df['short_historical_rates_3d'].apply(sum)
    df['long_cumulative_rate_3d'] = df['long_historical_rates_3d'].apply(sum)

    # Additional cumulative sums for 30/7/3 days (hourly data)
    def sum_last_n_days(values, days):
        try:
            hours = days * 24
            return sum(values[-hours:])
        except Exception:
            return 0

    main_days = CONFIG['funding_historical_days']
    # Main window diff uses full (already windowed) arrays; also compute 7d/3d diffs from prepared arrays
    df['short_cum_main'] = df['short_cumulative_rate']
    df['long_cum_main'] = df['long_cumulative_rate']
    df[f'cumulative_rate_diff_{main_days}d'] = df['short_cum_main'] - df['long_cum_main']
    df['cumulative_rate_diff_7d'] = df['short_cumulative_rate_7d'] - df['long_cumulative_rate_7d']
    df['cumulative_rate_diff_3d'] = df['short_cumulative_rate_3d'] - df['long_cumulative_rate_3d']

    # Identify amplitude as the maximum between two exchanges or the values with more data available
    # Assigning initial values
    df['mean_daily_amplitude'] = df[['mean_daily_amplitude_x', 'mean_daily_amplitude_y']].max(axis=1)
    df['max_daily_amplitude'] = df[['max_daily_amplitude_x', 'max_daily_amplitude_y']].max(axis=1)
    df['amplitude_days'] = df['amplitude_days_x']

    # Updating values based on conditions
    condition_1 = df['amplitude_days_x'] > df['amplitude_days_y']
    condition_2 = df['amplitude_days_y'] > df['amplitude_days_x']

    df.loc[condition_1, 'mean_daily_amplitude'] = df['mean_daily_amplitude_x']
    df.loc[condition_1, 'max_daily_amplitude'] = df['max_daily_amplitude_x']
    df.loc[condition_1, 'amplitude_days'] = df['amplitude_days_x']
    df.loc[condition_2, 'mean_daily_amplitude'] = df['mean_daily_amplitude_y']
    df.loc[condition_2, 'max_daily_amplitude'] = df['max_daily_amplitude_y']
    df.loc[condition_2, 'amplitude_days'] = df['amplitude_days_y']

    main_days = CONFIG['funding_historical_days']
    main_diff_col = f'cumulative_rate_diff_{main_days}d'
    return df[
        ['pair', f'APY_historical_average', 'short_exchange', 'long_exchange',
         'mean_daily_amplitude', 'max_daily_amplitude', 'amplitude_days',
         'short_cumulative_rate', 'long_cumulative_rate',
         'short_cumulative_rate_7d', 'long_cumulative_rate_7d',
         'short_cumulative_rate_3d', 'long_cumulative_rate_3d',
         'short_historical_rates', 'long_historical_rates',
         'short_historical_rates_7d', 'long_historical_rates_7d',
         'short_historical_rates_3d', 'long_historical_rates_3d',
         main_diff_col, 'cumulative_rate_diff_7d', 'cumulative_rate_diff_3d']]


def create_spot_perp_opportunites_df(perpetual_exchange, perpetual_rates_df, spot_pairs_df):
    """
   Creates a dataframe of Spot-Perpetual trading opportunities by merging perpetual and spot dataframes

   Args:
       perpetual_exchange (str): Name of the perpetual exchange.
       perpetual_rates_df (pd.DataFrame): DataFrame of funding rates for perpetual_exchange.
       spot_pairs_df (pd.DataFrame): DataFrame of spot trading pairs.

   Returns:
       pd.DataFrame: DataFrame containing Spot-Perpetual trading opportunities.
   """
    # Rename pair column to spot_pair in spot data dataframe (copy)
    spot_pairs_df = spot_pairs_df.rename(columns={'pair': 'spot_pair'})

    # Create spot_pair column out of perpetual pair by splitting the string with ':'
    perpetual_rates_df['spot_pair'] = perpetual_rates_df['pair'].str.split(':').str.get(0)

    # Filter data below the threshold; if 'rate' is missing, approximate using last historical point
    if 'rate' not in perpetual_rates_df.columns:
        perpetual_rates_df['historical_rates'] = perpetual_rates_df['historical_rates'].fillna('[]').apply(ast.literal_eval)
        perpetual_rates_df['rate'] = perpetual_rates_df['historical_rates'].apply(lambda lst: lst[-1] if isinstance(lst, list) and len(lst) > 0 else 0)
    perpetual_rates_df = perpetual_rates_df[perpetual_rates_df['rate'].abs() > CONFIG['funding_rate_threshold']]

    # Merge perpetual and spot dataframes
    spot_perp_df = pd.merge(perpetual_rates_df, spot_pairs_df, on='spot_pair', how='inner')

    # Add the column with the perpetual exchange name
    spot_perp_df['perp_exchange'] = perpetual_exchange

    # Format historical rates and calculate average APY out of them
    spot_perp_df['historical_rates'] = spot_perp_df['historical_rates'].fillna('[]').apply(ast.literal_eval)
    spot_perp_df['APY_historical_average'] = 365 * spot_perp_df['historical_rates'].apply(sum) / CONFIG['funding_historical_days']

    # Additional cumulative sums for 30/7/3 days
    def sum_last_n_days(values, days):
        try:
            hours = days * 24
            return sum(values[-hours:])
        except Exception:
            return 0

    main_days = CONFIG['funding_historical_days']
    spot_perp_df[f'cum_sum_{main_days}d'] = spot_perp_df['historical_rates'].apply(lambda v: sum_last_n_days(v, main_days))
    # Removed 7d and 3d cumulative sums per request

    # Round APY
    spot_perp_df['APY_historical_average'] = spot_perp_df['APY_historical_average'].round(decimals=2)

    return spot_perp_df[
        ['pair', 'rate', 'APY_historical_average', 'perp_exchange', 'spot_exchange',
         'mean_daily_amplitude', 'max_daily_amplitude', 'amplitude_days', 'historical_rates',
         f'cum_sum_{main_days}d']]


def filter_and_sort_rates(df, negative=False):
    """
    Filters and sorts DataFrame with Spot-Perpetual trading opportunities based on specified conditions.

    Args:
        df (pd.DataFrame): DataFrame containing Spot-Perpetual trading opportunities
        negative (bool): Specifies whether to filter dataframes with positive or negative rates.

    Returns:
        pd.DataFrame: Filtered and sorted DataFrame.
    """
    if negative:
        df[f'APY_historical_average'] *= -1
        filtered_df = df[df['rate'] < 0]
        sorted_df = filtered_df.sort_values(by='rate', ascending=True, ignore_index=True)
    else:
        filtered_df = df[df['rate'] > 0]
        sorted_df = filtered_df.sort_values(by='rate', ascending=False, ignore_index=True)

    return sorted_df


def remove_leading_numbers(trading_pair):
    """
    Removes leading numbers starting with '10', '100', '1000', etc., from a trading pair string.

    Args:
    - trading_pair (str): The trading pair string containing currency names and possibly leading numbers.

    Returns:
    - str: The trading pair string with leading numbers removed.
    """
    return re.sub(r'^(10+)', '', trading_pair)

