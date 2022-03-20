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
from pkg.core.SaleItem import SaleItem

class test_SaleItem(unittest.TestCase):

    def test_random(self):
        '''
        Randomizes a number of SaleItem object and checks that calculated
        properties match expected values
        '''
        import string
        letters = string.ascii_letters

        for _ in range(100):
            brokerage  = ''.join(random.choice(letters) for i in range(random.randint(1,30)))
            ticker     = ''.join(random.choice(letters) for i in range(random.randint(3,5)))
            sale_price = random.random()*100
            amount     = random.randint(1,100000000)

            # Random dates need to be be controlled for correctness. We create some base dates and then
            # we add a random number of days offset from the base as the buy date and a larger random
            # offset for the sell date
            base_dates = ['1900-01-01','1950-03-07','1970-05-10','1995-10-02','2006-07-12','2020-03-04']
            date_acquired = date.fromisoformat(random.choice(base_dates)) + timedelta(days=random.randint(0,1000))
            date_sold = date_acquired + timedelta(days=random.randint(0,500))
            cost_basis = amount * random.random()*100
            lot_id     = ''.join(random.choice(letters) for i in range(random.randint(3,5)))

            sale_item = SaleItem(
                brokerage=brokerage,
                ticker=ticker,
                sale_price=sale_price,
                amount=amount,
                date_acquired=str(date_acquired),
                date_sold=str(date_sold),
                cost_basis=cost_basis,
                lot_id=lot_id
            )

            wash          = bool(random.randint(0,1))
            dis_wash_loss = random.random()*20
            comm          = random.random()*5

            sale_item.wash = wash
            sale_item.dis_wash_loss = dis_wash_loss
            sale_item.comm = comm

            # Check resultant properties
            net_proceeds = amount*sale_price-comm
            gain = amount*sale_price-cost_basis-comm
            allowed_loss = 0
            if gain < 0 and wash:
                allowed_loss = min(0,gain + dis_wash_loss)
            gain_per_share = gain/amount
            short_term = (date_sold - date_acquired) < timedelta(days=366) 
            self.assertEqual(sale_item.net_proceeds,net_proceeds)
            self.assertEqual(sale_item.gain,gain)
            self.assertEqual(sale_item.allowed_loss,allowed_loss)
            self.assertEqual(sale_item.gain_per_share,gain_per_share)
            self.assertEqual(sale_item.short_term,short_term)

