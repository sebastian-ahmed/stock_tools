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
                date=rand_date
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
                'date':str(rand_date)
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
        