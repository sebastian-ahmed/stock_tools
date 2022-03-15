from pkg.core.StockTransactor import StockTransactor

def main():
    file_name = './pkg/examples/stocks_example.csv'
    stock_data = StockTransactor(file_name)

    stock_data.print_report(date_range=('2022-01-01','2023-03-12'))
    stock_data.write_report(date_range=('2022-01-01','2023-03-12'))
    
if __name__ == '__main__':
    main()