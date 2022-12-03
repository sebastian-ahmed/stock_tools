# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

import datetime
from pkg.core.LoggingWrap import log_error

class StockTransaction:
    '''
    Defines a stock transaction for a given brokerage and ticker symbol. This means
    it is possible to separate transactions for the same security but within different
    brokerage accounts
    '''

    @classmethod
    def from_dict(cls,in_dict):
        '''
        Returns a StockTransaction object from a dict representation (e.g. JSON)
        '''
        lot_ids = []
        if 'lot_ids' in in_dict.keys():
            if in_dict['lot_ids']: # CSV will provide a None value as key is not optional
                lot_ids = in_dict['lot_ids'].split(':')

        add_basis = 0.0
        if 'add_basis' in in_dict.keys(): 
            if in_dict['add_basis']:  # CSV will provide a None value as key is not optional
                add_basis = in_dict['add_basis']

        return cls(
            tr_type = str(in_dict['tr_type']),
            ticker = str(in_dict['ticker']),
            amount = float(in_dict['amount']),
            price = float(in_dict['price']),
            date = str(in_dict['date']),
            comm = float(in_dict['comm']),
            brokerage = str(in_dict['brokerage']),
            add_basis = float(add_basis),
            lot_ids = lot_ids
        )

    def __init__(
        self,
        tr_type:str = 'buy',
        ticker:str = None,
        amount:float = 0,
        price:float = 0.0,
        date:str = None,
        comm:float = 0.0,
        brokerage:str = None,
        add_basis:float = 0.0,
        lot_ids:list=[],
        sell_all:bool=False
        ):

        self.ticker = ticker
        self.amount = amount
        self.price  = price
        self.comm   = comm
        self.brokerage = brokerage
        self.add_basis = add_basis
        self.lot_ids = lot_ids
        self.sell_all = sell_all # Only applies to tr_type=='sell'

        # Checks
        if self.sell_all == True and tr_type is not 'sell':
            raise RuntimeError('Specified sell_all=True with a buy transaction')

        self._sold = False # Denotes that this transaction has been sold

        if not date:
            self.date = str(datetime.date.today())
        else:
            if isinstance(date,str):
                try:
                    self.date = str(datetime.date.fromisoformat(date))
                except:
                    log_error(f'Provided date "{date}" is not a valid ISO format YYYY-MM-DD')
                    raise
            else:
                raise ValueError('Date provided is not a supported type datetime.date or string ISO format YYYY-MM-DD')

        if isinstance(tr_type,str):
            if tr_type.lower() in ['buy','sell']:
                self.tr_type = tr_type.lower()
            else:
                raise ValueError(f"Invalid transcation value={tr_type} must be a string 'buy' or 'sell'")

        if self.tr_type == 'buy' and len(self.lot_ids) > 1:
            raise ValueError(f'Invalid lot_ids value of {self.lot_ids}. Buy transactions cannot contain more than one lot_id value')

        # Remove any empty string entries
        self.lot_ids = [x for x in self.lot_ids if len(x)>0]

    @property
    def is_sold(self)->bool:
        '''
        Reflects whether this transaction has been fully sold. Relevant if the transaction
        is a buy type
        '''
        return self._sold

    @is_sold.setter
    def is_sold(self,val:bool):
        self._sold = bool(val)

    @property
    def lot_id(self)->str:
        '''
        If this is a buy transaction returns the lot id if assigned. In all other
        cases, returns None
        '''
        if self.tr_type == 'buy' and len(self.lot_ids) > 0:
            return str(self.lot_ids[0])
        return None

    def asdict(self)->dict:
        '''
        Returns a dict view of this object where all values are strings enabling
        serialization
        '''
        odict = {}
        odict['tr_type']   = str(self.tr_type)
        odict['ticker']    = str(self.ticker)
        odict['amount']    = str(self.amount)
        odict['price']     = str(self.price)
        odict['date']      = str(self.date)
        odict['comm']      = str(self.comm)
        odict['brokerage'] = str(self.brokerage)
        odict['is_sold']   = str(self.is_sold)
        odict['add_basis'] = str(self.add_basis)
        odict['lot_ids']   = ':'.join(self.lot_ids)
        return odict

    def __str__(self):
        ostr = 'StockTransaction  '
        asdict = self.asdict()
        for elem in asdict:
            ostr += str(elem) + '=' + str(asdict[elem]) + ','
        return ostr[:-1]
