# Funding Rate Arbitrage scanner

This project is designed for analyzing funding rates and identifying potential Perpetual-Perpetual and Perpetual-Spot arbitrage opportunities.


## Introduction

This project fetches funding rate data from configured cryptocurrency exchanges and analyzes it to identify potential trading opportunities. You can use any exchange from the CCXT library. For a list of supported exchange IDs, refer to:
https://docs.ccxt.com/#/?id=exchanges

It provides functionality to fetch and save:
- Current funding rate data
- Historical funding rate data
- Daily volatility data


## Installation

Clone the repository:
```bash
git clone https://github.com/supervik/funding-rate-arbitrage-scanner.git
```
Navigate to the project directory:
 ```bash
 cd funding-rate-arbitrage-scanner
 ```
Install dependencies:
 ```bash
pip install -r requirements.txt
 ```
Run the main script:
```bash
python funding_rate_arbitrage_scanner.py
```

## Configuration

Configure the project according to your requirements by editing the `config.py` file. The configuration options include specifying the list of exchanges, file format, historical data parameters, and more.

Date-based subfolders (default):
- Data and results are written to `funding_data/<date>/{data|result}` by default.
- Control the format via `use_date_subfolder` (default True) and `date_subfolder_format` (default `%Y%m%d`).
- Optionally set `date_subfolder` manually to override today.

To efficiently utilize the project, follow these steps:

1. **Fetch and Save Data:** To initiate the fetching and saving of funding rate data from exchanges, set the `fetch_and_save_data` parameter in the `config.py` file to `True`. To speed up data collection, you can set `fetch_current_rate` to `False` to skip current-rate requests and only fetch historical and amplitude data. Data is stored under `funding_data/<date>/data` by default.
2. **Analysis:** After fetching and saving the data, set the `fetch_and_save_data` parameter to `False`. Now, you can run analysis multiple times on the saved data by setting the `analyze_data_from_files` parameter to `True`. This enables the script to analyze the previously saved data from files without the need to fetch it again.


## Analysis

The analysis results are stored in the `funding_data/<date>/result` folder.

For Perpetual-Perpetual opportunities, the analysis generates a file named `result_perp_perp_*` with the following columns:

- **pair**: The trading pair involved in the opportunity
- **rate_diff**: The current difference in funding rates between the short and long exchanges
- **APY_historical_average**: The average APY calculated from historical rates over the past N days. The number of days configured by the `funding_historical_days` parameter
- **cumulative_rate_diff_30d / 7d / 3d**: Out-of-sample cumulative sums of the short-long historical rate differences for the last 30, 7 and 3 days (hourly data)
- **short_exchange**: The exchange with the higher funding rate where you are supposed to open a Short order
- **long_exchange**: The exchange with the lower funding rate where you are supposed to open a Long order
- **mean_daily_amplitude**: The average daily amplitude of the trading pair. Amplitude is the percentage difference between the daily high and low prices. Higher amplitudes indicate greater asset volatility. The number of days for calculation is configured by the `amplitude_days` parameter
- **max_daily_amplitude**: The maximum daily amplitude of the trading pair
- **short_rate**: The current funding rate of the short exchange
- **long_rate**: The current funding rate of the long exchange
- **short_cumulative_rate**: The cumulative funding rate of the short exchange
- **long_cumulative_rate**: The cumulative funding rate of the long exchange
- **short_historical_rates**: List of historical funding rates of the short exchange. The number of days configured by the `funding_historical_days` parameter
- **long_historical_rates**: List of historical funding rates of the long exchange. The number of days configured by the `funding_historical_days` parameter

For Perpetual-Spot arbitrage opportunities, the analysis generates two files named `result_spot_perp_positive_*` and `result_spot_perp_negative_*` for positive and negative funding rates, respectively, with the following columns:
- **pair**: The trading pair involved in the opportunity
- **rate**: The current funding rate on the perpetual exchange
- **APY_historical_average**: The average APY calculated from historical rates over the past N days. The number of days configured by the `funding_historical_days` parameter
- **cum_sum_30d / 7d / 3d**: Out-of-sample cumulative sums for the last 30, 7 and 3 days (hourly data)

### Ad-hoc current-rate fetcher

To quickly fetch only current funding rates from a limited set of exchanges and/or pairs, use `fetch_current_rates.py` with `config_current_rates.py`:

```bash
python fetch_current_rates.py
```

Configure `config_current_rates.py`:
- `perpetual_exchanges`: limited exchange ids
- `pairs_filter`: optional list of pairs (e.g. `['BTC/USDT:USDT']`) to limit requests and speed up fetching
- **perp_exchange**: The perpetual exchange where you are supposed to open a Short order if the rate is positive and Long order if the rate is negative
- **spot_exchange**: Spot exchanges where you can hedge the opportunity: open a Buy order if the rate is positive and Sell if the rate is negative
- **mean_daily_amplitude**: The average daily amplitude of the trading pair. Amplitude is the percentage difference between the daily high and low prices. Higher amplitudes indicate greater asset volatility. The number of days for calculation is configured by the `amplitude_days` parameter
- **max_daily_amplitude**: The maximum daily amplitude of the trading pair
- **historical_rates**: List of historical funding rates. The number of days configured by the `funding_historical_days` parameter
