# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

import unittest
import random
from datetime import date,timedelta
from pkg.core.StockTransactor import StockTransactor
from pkg.core.SaleItem import SaleItem

class test_StockTransactor_API(unittest.TestCase):
    '''
    Test-cases which exercise the programmatical interface
    '''

    def setUp(self) -> None:
        self.st = StockTransactor(input_file_name='pkg/unittest/input_files/blank.json')
        return super().setUp()

    def test_basic(self):
        '''
        Checks the basic buy and sell interface and checks resulting
        holdings and sales
        '''
        self.st.buy(brokerage='AAA_Brokerage',ticker='ACME',amount=100,price=10,date='2000-01-01')
        self.st.buy(brokerage='AAA_Brokerage',ticker='ACME',amount=25,price=10,date='2001-02-02')
        self.st.buy(brokerage='BBB_Brokerage',ticker='ACME',amount=50,price=20,date='2000-02-01')
        self.st.buy(brokerage='BBB_Brokerage',ticker='ACME',amount=25,price=20,date='2001-03-02')
        self.assertEqual(self.st.get_num_shares(brokerage='AAA_Brokerage',ticker='ACME'),125)
        self.assertEqual(self.st.get_num_shares(brokerage='BBB_Brokerage',ticker='ACME'),75)
        self.assertEqual(self.st.get_num_shares(ticker='ACME'),200)

        self.assertEqual(len(self.st.current_holdings['AAA_Brokerage']['ACME']),2)
        self.assertEqual(len(self.st.current_holdings['BBB_Brokerage']['ACME']),2)

        # Now sell some ACME stock from each brokerage. Only FIFO ordering is supported
        # by the API
        self.st.sell(brokerage='AAA_Brokerage',ticker='ACME',amount=100,price=20)
        self.st.sell(brokerage='BBB_Brokerage',ticker='ACME',amount=50,price=30)

        # Check that the number of remaining shares matches the expected amounts
        # after the sales
        self.assertEqual(self.st.get_num_shares(brokerage='AAA_Brokerage',ticker='ACME'),25)
        self.assertEqual(self.st.get_num_shares(brokerage='BBB_Brokerage',ticker='ACME'),25)
        self.assertEqual(self.st.get_num_shares(ticker='ACME'),50)

        # Check the sale items
        today = str(date.today())
        aaa_exp_sale_item = SaleItem(brokerage='AAA_Brokerage',ticker='ACME',sale_price=20,amount=100,date_acquired='2000-01-01',date_sold=today,cost_basis=1000)
        bbb_exp_sale_item = SaleItem(brokerage='BBB_Brokerage',ticker='ACME',sale_price=30,amount=50,date_acquired='2000-02-01',date_sold=today,cost_basis=1000)
        self.assertEqual(self.st.sales['AAA_Brokerage']['ACME'][0].asdict(),aaa_exp_sale_item.asdict())
        self.assertEqual(self.st.sales['BBB_Brokerage']['ACME'][0].asdict(),bbb_exp_sale_item.asdict())


class test_StockTransactor_File(unittest.TestCase):
    '''
    Test-cases which exercise the standard file-input interface
    '''

    def test_ws_1(self):
        '''
        Tests a wash sale scenario of pre-buying shares before a loss sale
        '''
        st = StockTransactor(input_file_name='pkg/unittest/input_files/test-ws-1.json')
        # FIXME: Replace with expected results file.
        self.assertEqual(st.current_holdings['MyBroker_A']['TQQQ'].data[0].add_basis,3604)
        self.assertEqual(st.current_holdings['MyBroker_A']['TQQQ'].data[1].add_basis,2703)
        self.assertEqual(st.current_holdings['MyBroker_A']['TQQQ'].data[2].add_basis,2703)
