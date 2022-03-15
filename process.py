from pkg.core.WinWrap import WinWrap
from pkg.core.Cla import proc_cla
from pkg.core.StockTransactor import StockTransactor

'''
Top-level application script which processes a stock transactions file and generates
reports. Reports are controlled via command line arguments. Note that richer control
of reports is available through programmatical use of the stock_tools core libraries
'''

def main():
    args = proc_cla(iparser=None,descr='Stock transaction file processing script')

    print(f'Running with arguments: {args}')
    stock_data = StockTransactor(input_file_name=args.infile,output_file_name=args.outfile)

    stock_data.print_report(date_range=(args.date_start,args.date_end),fetch_quotes=args.fetch_quotes)
    stock_data.write_report(date_range=(args.date_start,args.date_end),fetch_quotes=args.fetch_quotes)

if __name__ == '__main__':
    with WinWrap(main) as wmain:
        wmain()