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
from pkg.core.StockTransaction import StockTransaction

class test_StockTransaction(unittest.TestCase):

    def test_non_numerical_defaults(self):
        '''
        Checks default values for non-numerical fields
        '''
        st = StockTransaction()
        self.assertEqual(st.date,str(date.today()))
        self.assertEqual(st.tr_type,'buy')

    def test_random(self):
        '''
        Randomizes initialization and checks for expected values. Also checks the
        asdict() method returns the correct value
        '''
        import string
        letters = string.ascii_letters

        for _ in range(100):
            tr_type   = random.choice(['sell','buy'])
            ticker    = ''.join(random.choice(letters) for i in range(random.randint(3,5)))
            amount    = random.randint(1,100000000)
            price     = random.random()
            comm      = random.random()
            brokerage = ''.join(random.choice(letters) for i in range(random.randint(1,30)))
            is_sold   = bool(random.randint(0,1))
            add_basis = random.random()
            sale_ids  = random.choice(['','0','1:2','1:2:3:4','2:5:1:3'])
            buy_id    = ''.join(random.choice(letters) for i in range(random.randint(1,30)))
            if tr_type == 'sell':
                lot_ids = sale_ids
            else:
                lot_ids = buy_id
            lot_ids = lot_ids.split(':')

            days_offset = random.randint(-500,500)
            dd = timedelta(days=days_offset)

            rand_date = str(date.today()+dd)

            st = StockTransaction(
                tr_type=tr_type,
                ticker=ticker,
                amount=amount,
                price=price,
                comm=comm,
                brokerage=brokerage,
                date=rand_date,
                lot_ids=lot_ids
            )

            # update post-init properties
            st.is_sold = is_sold
            st.add_basis = add_basis

            self.assertEqual(st.tr_type,tr_type)
            self.assertEqual(st.ticker,ticker)
            self.assertEqual(st.amount,amount)
            self.assertEqual(st.price,price)
            self.assertEqual(st.comm,comm)
            self.assertEqual(st.brokerage,brokerage)
            self.assertEqual(st.is_sold,is_sold)
            self.assertEqual(st.add_basis,add_basis)
            self.assertEqual(st.date,rand_date)
            # lot_ids will remove empty id strings, so for these cases we
            # need to adjust the expected value
            filtered_lot_ids = [x for x in lot_ids if len(x)>0]
            self.assertEqual(st.lot_ids,filtered_lot_ids)

            # Check properties
            self.assertEqual(st.is_sold,is_sold)
            self.assertEqual(st.add_basis,add_basis)
            if st.tr_type == 'sell' or len(filtered_lot_ids) == 0:
                lot_id = None
            else:
                lot_id = filtered_lot_ids[0]
            self.assertEqual(st.lot_id,lot_id)

            # Check asdict()
            asdict = st.asdict()
            ref_dict = {
                'tr_type':str(tr_type),
                'ticker':str(ticker),
                'amount':str(amount),
                'price':str(price),
                'comm':str(comm),
                'brokerage':str(brokerage),
                'is_sold':str(is_sold),
                'add_basis':str(add_basis),
                'date':str(rand_date),
                'lot_ids':':'.join(filtered_lot_ids)
            }
            self.assertEqual(sorted(list(asdict.keys())),sorted(list(ref_dict.keys())))
            self.assertEqual(asdict,ref_dict)

    def test_errors_invalid_date(self):
        '''
        Checks that initializing with an invalid date format raises an exception
        '''
        def invalid_init():
            _ = StockTransaction(date='7-23-2022')

        self.assertRaises(ValueError,invalid_init)

    def test_errors_invalid_type(self):
        '''
        Checks that initializing with an invalid transaction type raises an exception
        '''
        def invalid_init():
            _ = StockTransaction(tr_type='hodl')

        self.assertRaises(ValueError,invalid_init)
        