# Overview

`stock_tools` is a set of utilities for helping to manage multi-brokerage stock trading portfolios with the main functionality generating stock sale reporting for tax purposes. Specifically, by simply providing an input file of all stock trades of interest, `stock_tools` will generate a report of sale items with the following characteristics:
- Supports a default sale ordering of "first-in-first-out' (FIFO) stock buys as well as support for sales which target ordering of specified buy lots
- When a sale covers multiple prior buy lots, a discrete sale item is created for each input buy lot. This allows for breaking out parts of the sale which may be long-term vs short-term, have different cost-basis amounts, and different commissions
- Correctly determines **wash sales** including the amounts of loss disallowed by the wash-sale. Further, any disallowed wash sale amounts are then added as additional cost-basis amounts for any downstream buys of that stock
    - When a wash-sale-triggering buy is a smaller lot than the wash sale, the disallowed loss amount is only based on the number of stocks of the buy lot
    - Wash sales are analyzed across different brokerage entries as required by the tax code
- Provision for additional basis added to stock purchase transaction description such as for ESPP disqualifying disposition (where the discount gain is reported as W-2 income and must be added to IRS reported cost-basis)
- Provision for entering custom commands to describe events such as **stock splits**. Stock splits are retroactively applied to relevant buy lots in the input stock transaction history.
- Provides additional output formats of the sales summary including JSON serialized output and HTML 
- Includes a report of holdings optionally with current stock prices and resulting valuation and gain per holding (by connecting directly to the Yahoo Finance web API)

NOTE: Dividend re-investment plans (DRIPs) are assumed to be modelled as regular stock purchase transactions. Regular dividend payments (1099-DIV) are orthogonal to stock sale reporting and are not considered as part of `stock_tools`

# Contents
- [Overview](#overview)
- [Contents](#contents)
- [Usage](#usage)
  - [Required Python packages](#required-python-packages)
  - [Using the run-script](#using-the-run-script)
  - [Using the StockTransactor Class](#using-the-stocktransactor-class)
  - [Running examples](#running-examples)
- [Example Output](#example-output)
- [Sale ordering](#sale-ordering)
- [Notes about calculations](#notes-about-calculations)
- [Special commands](#special-commands)
  - [SPLIT](#split)
  - [Programmatical commands](#programmatical-commands)
# Usage
There are two general usage modes. The simplest and recommended mode is to to use the included top-level run-script. Advanced users may programmatically use the core processing class as part of their own custom script.

## Required Python packages
In order to use `stock_tools` you must have the following Python environment installed on your system:
- Python version 3.6 or newer
- The following additional packages which can be installed using `pip install <package>`
    - `yfinance`
    - `prettytable`

## Using the run-script
On a command line, assuming an input file stocks.csv, simply run:
```
python process.py --infile stocks.csv --fetch_quotes
```
This will generate the default report file `report_consolidated.txt` which includes the values and gains of resulting holdings based on current stock prices. In addition to this, the following files are created which capture the sales and holdings summary tables:
- `report_sales.json` : A serialized version of the sales output table in JSON format
- `report_sales.html` : An HTML output version of the sales output table
- `report_holdings.json` : A serialized version of the holdings output table in JSON format
- `report_holdings.html` : An HTML output version of the holdings output table

Note that the base-name `report` can be changed using the `--outfile` command line argument

Full usage can be printed via the `--help` command line option, and is show here for convenience:
```
options:
  -h, --help            show this help message and exit
  --infile <stock transaction file>
                        Specifies the file which contains stock transactions. Supported formats are .csv and .json
  --outfile <output report file>
                        Optionally specifies an output file base-name for the reports
  --date_start <YYYY-MM-DD>
                        Optionally specifies a start date for report generation. If not specified, the date of the first transaction is used
  --date_end <YYYY-MM-DD>
                        Optionally specifies an end date for report generation. If not specified, the date of the last transaction is used
  --fetch_quotes        Includes current values based on current stock prices. Note: This causes a slow-down in report generation due to web API calls
  ```

## Using the StockTransactor Class
This method involves creating a `StockTransactor` object with an input file argument. This initialization step will cause the `StockTransactor` to read the input file, and perform the processing of transactions. Following this, the user can generate reports to the terminal or to a file. Currently there ar two input formats supported: `CSV` and `JSON`. Examples of both formats can be found in the [examples directory](./pkg/examples/).

Below is a snippet which shows the minial steps:
```python
from pkg.core.StockTransactor import StockTransactor

stock_data = StockTransactor('./pkg/examples/stocks_example.csv')

# Print the sales report to the terminal as well as to the file
# with default output file-name
stock_data.print_report()
stock_data.write_report()
```

## Running examples
You can run either the CSV or JSON examples from the command line as follows. First make sure you are at the top-level directory of this project:

- CSV input file example
```
python -m pkg.examples.csv_input
```
- JSON input file example
```
python -m pkg.examples.json_input
```

# Example Output
Below is the report output from running either of the above examples with the `--fetch_quotes` option enabled. Note that the table in the "SALES REPORT" section lists sales which can be reported for tax purposes. The "HOLDINGS REPORT" section is informational and useful in the sense that you can see the holdings with gains and losses across all your brokerage accounts.

```
Running with arguments: Namespace(date_end=None, date_start=None, fetch_quotes=True, infile='pkg/examples/stocks_example.json', outfile=None)
Reading file pkg/examples/stocks_example.json as JSON
INFO: Encountered command: SPLIT with arguments ['QCOM', '2', '2025-04-15']
INFO: Encountered command: SPLIT with arguments ['QCOM', '10', '2023-04-15']
INFO: Encountered command: SPLIT with arguments ['QCOM', '5', '2024-04-15']
INFO: Wash Sale detected for SPY with sale date 2022-06-25 with wash trigger buy on 2022-07-15
INFO: Wash Sale detected for SPY with sale date 2022-07-16 with wash trigger buy on 2022-07-15
INFO: Wash Sale detected for SPY with sale date 2022-07-16 with wash trigger buy on 2022-08-15
================================================================================
=                                 SALES REPORT                                 =
================================================================================
Date range: None to None

+------------+--------+------------+--------+---------------+------------+------------+------------+-------+------+---------------+----------+----------+----------------+--------------+--------+
| brokerage  | ticker | sale_price | amount | date_acquired | date_sold  | cost_basis | short_term |  wash | comm | dis_wash_loss | proceeds |   gain   | gain_per_share | allowed_loss | lot_id |
+------------+--------+------------+--------+---------------+------------+------------+------------+-------+------+---------------+----------+----------+----------------+--------------+--------+
| MyBroker_B |  SPY   |   500.0    |  75.0  |   2022-03-12  | 2022-06-25 |  75000.0   |    True    |  True | 5.0  |    37500.0    | 37495.0  | -37500.0 |     -500.0     |     0.0      |  None  |
| MyBroker_B |  SPY   |   500.0    |  25.0  |   2022-03-12  | 2022-07-16 |  25005.0   |    True    |  True | 0.0  |    12505.0    | 12500.0  | -12505.0 |     -500.2     |     0.0      |  None  |
| MyBroker_B |  SPY   |   500.0    |  75.0  |   2022-07-15  | 2022-07-16 |  60005.0   |    True    |  True | 5.0  |    7501.67    | 37495.0  | -22505.0 |    -300.07     |  -15003.33   |  None  |
| MyBroker_A |  TQQQ  |   200.0    |  25.0  |   2022-04-05  | 2023-03-12 |   3005.0   |    True    | False | 0.0  |      0.0      |  5000.0  |  1995.0  |      79.8      |     0.0      |   2    |
| MyBroker_A |  TQQQ  |   200.0    |  25.0  |   2022-04-01  | 2023-03-12 |   2755.0   |    True    | False | 5.0  |      0.0      |  4995.0  |  2245.0  |      89.8      |     0.0      |   1    |
| MyBroker_A |  TQQQ  |   200.0    |  50.0  |   2022-03-12  | 2023-03-12 |   5000.0   |   False    | False | 5.0  |      0.0      |  9995.0  |  5000.0  |     100.0      |     0.0      |   0    |
+------------+--------+------------+--------+---------------+------------+------------+------------+-------+------+---------------+----------+----------+----------------+--------------+--------+

Total proceeds                = $107480.0
Net gain (raw)                = $-63270.0
Net gain (adjusted)           = $-5763.33
Total disallowed wash amounts = $57506.67

================================================================================
=                                HOLDINGS REPORT                               =
================================================================================

Brokerage: MyBroker_A
+--------+---------+------------+-------------+-----------+-----------+----------------------+----------------------+
| ticker |  amount | cost-basis | added-basis | cur-price | cur-value |       cur-gain       |  cur-adjusted-gain   |
+--------+---------+------------+-------------+-----------+-----------+----------------------+----------------------+
|  TQQQ  |   50.0  |   5000.0   |     0.0     |   50.06   |   2503.0  |  -2497.0 (-49.94%)   |  -2497.0 (-49.94%)   |
|  QCOM  | 10000.0 |  22000.0   |     0.0     |   152.83  | 1528300.0 | 1506300.0 (6846.82%) | 1506300.0 (6846.82%) |
|  QCOM  |  200.0  |  30000.0   |     0.0     |   152.83  |  30566.0  |    566.0 (1.89%)     |    566.0 (1.89%)     |
+--------+---------+------------+-------------+-----------+-----------+----------------------+----------------------+
Total Value         = $1561369.0
Total Adjusted Gain = $1504369.0 (2639.24%)

Brokerage: MyBroker_B
+--------+--------+------------+-------------+-----------+-----------+------------------+-------------------+
| ticker | amount | cost-basis | added-basis | cur-price | cur-value |     cur-gain     | cur-adjusted-gain |
+--------+--------+------------+-------------+-----------+-----------+------------------+-------------------+
|  SPY   |  25.0  |  10001.67  |   7501.67   |   441.07  |  11026.75 | 8526.75 (85.25%) |  1025.08 (10.25%) |
+--------+--------+------------+-------------+-----------+-----------+------------------+-------------------+
Total Value         = $11026.75
Total Adjusted Gain = $1025.08 (10.25%)
```
# Sale ordering
In order to generate reportable sale items, each sale transaction must be matched to one or more previous buy transactions which we can refer to as *buy lots*. This is an ordering concept. `stock_tools` supports two ordering modes which match the typical brokerage behaviors:
- Default ordering using first-in-first-out (FIFO) semantics:
  - The matching operation processes oldest buy lots first and works its way through to newer buy lots until all shares specified by the *amount* field in the input file are accounted for
  - No special instruction or configuration is required to enable the default mode
- User-defined ordering with specific buy lots:
  - In order to instruct the program to perform this user-defined ordering two things must be specified in the input file
    - Participating buy lots must be marked with an identifier using the *buy_ids* field (`buy_ids="<ID>"` for JSON input, or simply `<ID>` in the *buy_ids* column of a CSV file)
      - The identifiers must be unique within the ticker symbol namespace of a given brokerage. This means that if identifiers 'a' and 'b' were used for ticker XYZ, the same identifiers can safely be used for a different ticker, or for the same ticker in a different brokerage
    - The sale transaction which sells a specific lot or lots must be specified as a colon-delimited list/sequence using the *buy_ids* field
      - In the JSON input format, this will look as follows `buy_ids="<FIRST LOT ID>:<SECOND LOT ID>:..."`. The CSV input format is the same except the string is placed directly in the *buy_ids* column. The ordering follows the left to the right order.
      - It is up to the user to make sure that the specified lots have a sufficient amount of shares for the sale. The program will not switch to default ordering (to look for older buy lots) in order to complete the sale.
      - Both example input files demonstrate the format
      - Simply ommitting the *buy_ids* field treats the sale as FIFO ordering based
- In both cases, if there are insufficient shares to carry out the full sale, a `RuntimeError` exeption is raised

# Notes about calculations
As of now, there are some encoded rules in relation to gain and cost-basis calculations that users should be aware of:
- No rounding is performed in any calculations until a result is reported to the terminal or a file. 
- When a stock sale covers multiple buy lot transactions:
  - The sale transaction commission is applied to the *net proceeds* of the first generated sale item. It is not distributed across all generated sale items. From a tax-reporting perspective, this is arbitrary as long as it is accounted for and not double counted anywhere.
- When a sale transaction does not consume an entire buy lot, the buy transaction commission is not added to the cost basis of the buy. Only when a buy transaction is fully consumed, is the commission added to the cost basis. This also avoids double counting so that the commission is only ever applied to a single sale item.
- *net_proceeds*, *gain* and *gain_per_share* sale item fields all take into account commissions, but do not include disallowed wash-sale amounts. If a sale is a loss with a disallowed wash amount, the reportable loss value is captured in the *allowed_loss* field (which is an absolute value)
- Long-term designation occurs when the difference between the acquired date and sold date is greater or equal to 366 days

# Special commands
Both examples show example usage of the stock split special command. The general format of special commands is a single field of the format

```
!<COMMAND>#arg0#arg1#arg2#...
```

Each command has a unique number of arguments depending on the required semantics. The command lines may be placed anywhere in the input stock transaction file and in any order although it is recommended for documentation purposes that such commands are placed in chronological order along with stock transactions.

## SPLIT
The `SPLIT` command indicates a stock split event. The format of this command is as follows:

```
!SPLIT#<ticker>#<amount>#<date>
```

Consider a stock split for ticker IBM which is a 2:1 split (2 stocks created for every 1 stock) on July 10th 2022. The `JSON` and `CSV` version of the command line are shown below:

- CSV:
```
!SPLIT#IBM#2#2022-07-10
```
- JSON
```json
{cmd:"!SPLIT#IBM#2#2022-07-10"}
```

A reverse split (where the number of resulting shares is lower) must be expressed as a decimal, e.g., a 1-for-2 split would be denoted by an amount of 0.5 

## Programmatical commands
When using `stock_tools` in a programmatical way, commands may be called directly via the `StockTransactor` object as follows, where `<COMMAND>` is the full command string as described above

```python
st = StockTransactor(infile='my_stocks.json')
st.process_command(<COMMAND>)
st.rebuild() # Will force a re-processing of the input file
```
