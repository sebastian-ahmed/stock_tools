from datetime import date
class SaleItem:
    '''
    Defines a completed sale which is serializable
    '''

    def __init__(
        self,
        brokerage:str,
        ticker:str,
        sale_price:float,
        amount:float,
        date_acquired:str,
        date_sold:str,
        cost_basis:float,
        wash:bool=False):

        self.brokerage     = brokerage
        self.ticker        = ticker
        self.sale_price    = sale_price
        self.amount        = amount
        self.date_acquired = date_acquired
        self.date_sold     = date_sold
        self.cost_basis    = cost_basis
        self.short_term    = self.is_short_term(date_acquired,date_sold)
        self.wash          = wash

        self.comm  = 0.0 # Must be set after sale processing
        self.dis_wash_loss = 0.0 # Must be set during sale processing

    @property
    def proceeds(self)->float:
        '''
        Returns the proceeds from the sale minus any commissions
        '''
        return (self.amount * self.sale_price) - self.comm

    @property
    def gain(self)->float:
        '''
        Returns the gain (positive) or loss (negative) for this sale. Note that this
        does not take into account any wash sale disallowed loss amounts. Use the
        allowed_loss property to see the adjusted loss
        '''
        return self.__raw_gain()

    @property
    def allowed_loss(self)->float:
        '''
        If this sale constituted a wash sale, this property reflects the allowed
        loss after adjusting for the disallowed wash loss amount. In all other cases
        this property will reflect 0
        '''
        if self.wash and self.__raw_gain() < 0:
            return self.__raw_gain() + self.dis_wash_loss
        return 0.0

    @property
    def gain_per_share(self)->float:
        '''
        Returns the gain per share (positive) or loss (negative) for this sale
        '''
        return self.sale_price - (self.cost_basis/self.amount)

    @staticmethod
    def fields_list()->list:
        '''
        Unbound method which returns a list of strings matching the keys of the
        dict which would normally be available from the asdict() bound method call.
        Because this is a static method, it can be called un-bound for purposes
        such as generating report table headers
        '''
        return[
                'brokerage'     ,
                'ticker'        ,
                'sale_price'    ,
                'amount'        ,
                'date_acquired' ,
                'date_sold'     ,
                'cost_basis'    ,
                'short_term'    ,
                'wash'          , 
                'comm'          , 
                'dis_wash_loss' ,
                'proceeds'      ,
                'gain'          , 
                'gain_per_share',
                'allowed_loss'
        ]

    def asdict(self)->dict:
        '''
        Returns a dict view of this object where all values are strings enabling
        serialization
        '''
        odict = {}
        odict['brokerage']      = str(self.brokerage)
        odict['ticker']         = str(self.ticker)
        odict['sale_price']     = str(self.sale_price)
        odict['amount']         = str(self.amount)
        odict['date_acquired']  = str(self.date_acquired)
        odict['date_sold']      = str(self.date_sold)
        odict['cost_basis']     = str(self.cost_basis)
        odict['short_term']     = str(self.short_term)
        odict['wash']           = str(self.wash)
        odict['comm']           = str(self.comm)
        odict['dis_wash_loss']  = str(self.dis_wash_loss)
        odict['proceeds']       = str(self.proceeds)
        odict['gain']           = str(self.gain)
        odict['gain_per_share'] = str(self.gain_per_share)
        odict['allowed_loss']   = str(self.allowed_loss)

        return odict

    def ascsv(self)->str:
        '''
        Returns a CSV string view of this object
        '''
        asdict = self.asdict()
        ostr = ''
        for elem in asdict:
            ostr += str(asdict[elem]) + ","
        return ostr[:-1]

    def __str__(self):
        asdict = self.asdict()
        ostr = 'SaleItem  '
        for elem in asdict:
            ostr += str(elem) + '=' + str(asdict[elem]) + ','
        return ostr[:-1]

    def is_short_term(self,buy_date:str,sell_date:str)->bool:
        '''
        Given an ISO format YYYY-MM-DD buy date and sell date
        returns a boolean reflecting whether this was a short
        term (<365 day holding) sale
        '''
        d_buy = date.fromisoformat(buy_date)
        d_sell = date.fromisoformat(sell_date)
        d_diff = d_sell - d_buy
        return (d_diff.days < 365)

    def __raw_gain(self):
        return (self.amount * self.sale_price) - self.cost_basis
