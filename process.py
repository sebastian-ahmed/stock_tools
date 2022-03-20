# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

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