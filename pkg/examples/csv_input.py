# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

from pkg.core.StockTransactor import StockTransactor

def main():
    file_name = './pkg/examples/stocks_example.csv'
    stock_data = StockTransactor(file_name)

    stock_data.print_report(date_range=('2022-01-01','2024-12-31'))
    stock_data.write_report(date_range=('2022-01-01','2024-12-31'))
    
if __name__ == '__main__':
    main()