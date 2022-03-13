from pkg.core.StockTransactor import StockTransactor

def main():
    file_name = './pkg/examples/stocks_example.json'
    stock_data = StockTransactor(file_name)

    stock_data.print_sales_report()
    stock_data.print_holdings_report()
    stock_data.write_sales_file()
    
if __name__ == '__main__':
    main()