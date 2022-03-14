import datetime
from xmlrpc.client import boolean

class StockTransaction:
    '''
    Defines a stock transaction for a given brokerage and ticker symbol. This means
    it is possible to separate transactions for the same security but within different
    brokerage accounts
    '''

    @classmethod
    def from_dict(cls,dict):
        '''
        Returns a StockTransaction object from a dict representation (e.g. JSON)
        '''
        return cls(
            tr_type = str(dict['tr_type']),
            ticker = str(dict['ticker']),
            amount = float(dict['amount']),
            price = float(dict['price']),
            date = str(dict['date']),
            comm = float(dict['comm']),
            brokerage = str(dict['brokerage'])
        )

    def __init__(
        self,
        tr_type:str = 'buy',
        ticker:str = None,
        amount:float = 0,
        price:float = 0.0,
        date:str = None,
        comm:float = 0.0,
        brokerage:str = None):

        self.ticker = ticker
        self.amount = amount
        self.price  = price
        self.comm   = comm
        self.brokerage = brokerage

        self._sold = False # Denotes that this transaction has been sold
        self._add_basis = 0.0 # Additional basis such as from a previous wash sale

        if not date:
            self.date = str(datetime.date.today())
        else:
            if isinstance(date,str):
                try:
                    self.date = str(datetime.date.fromisoformat(date))
                except:
                    print(f'Date provided: is not a valid format YYYY-MM-DD')
                    raise
            else:
                raise ValueError('Date provided is not a supported type datetime.date or string ISO format YYYY-MM-DD')

        if isinstance(tr_type,str):
            if tr_type.lower() in ['buy','sell']:
                self.tr_type = tr_type.lower()
                return
        raise ValueError(f"Invalid transcation value={tr_type} must be a string 'buy' or 'sell'")

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
    def add_basis(self)->float:
        '''
        Returns any additional basis added to this sale such as from a previous wash sale
        '''
        return self._add_basis

    @add_basis.setter
    def add_basis(self,val:float):
        self._add_basis += val

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
        return odict

    def __str__(self):
        ostr = 'StockTransaction  '
        asdict = self.asdict()
        for elem in asdict:
            ostr += str(elem) + '=' + str(asdict[elem]) + ','
        return ostr[:-1]
