# Overview

`stock_tools` is a set of utilities for helping to manage stock trading portfolios. Currently, the main functionality includes a utility to generate stock sale reporting for tax purposes. Specifically, by simply providing an input file of all stock trades of interest, `stock_tools` will generate a report of sale items with the following characteristics:
- Uses the "first-in-first-out' (FIFO) ordering of stock buys. This means that when a sale is interpreted, we use the oldest buy lots first and follow that order
- When a sale covers multiple prior buy lots, a discrete sale item is created for each input buy lot. This allows for breaking out parts of the sale which may be long-term vs short-term, have different cost-basis amounts, and different commissions
- Correctly determines wash sales including the amounts of loss disallowed by the wash-sale. Further, any disallowed wash sale amounts are then added as additional cost-basis amounts for any downstream buys of that stock
    - When a wash-sale-triggering buy is a smaller lot than the wash sale, the disallowed loss amount is only based on the number of stocks of the buy lot
- Includes a report of holdings optionally with current stock prices and resulting valuation and gain per holding (by connecting directly to the Yahoo Finance web API)

# Usage
There are two general usage modes. The simplest mode is to to use the included top-level run-script. Otherwise, one may programmatically use the core processing class as part of a custom script.

## Using run-script
On a command line, assuming an input file stocks.csv, simply run:
```
python process.py --infile stocks.csv
```
This will generate the default report file `sales.txt`

For usage:
```
python process.py --help
```

## Using StockTransactor Class
This method involves creating a `StockTransactor` object with an input file argument. This initialization step will cause the `StockTransactor` to read the input file, and perform the processing of transactions. Following this, the user can generate reports to the terminal or to a file. Currently there ar two input formats supported: **CSV** and **JSON**. Examples of both formats can be found in the [examples directory](./pkg/examples/).

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
