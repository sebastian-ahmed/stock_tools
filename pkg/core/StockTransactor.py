import json
import os.path
from copy import deepcopy
from datetime import date,timedelta
from typing import Any, List
from collections import defaultdict

from pkg.core.StockTransaction import StockTransaction
from pkg.core.SaleItem import SaleItem
from pkg.core.Fifo import Fifo

class StockTransactor:
    '''
    Implements the processing layer of stock transactions. An object of this class is 
    responsible for the following operations:
    - Reading in of a stock transaction data file
    - Processing all transactions in the file
    - Reconciling sales relative to previous purchases using First-in-first-out (FIFO) semantics
    - Error checks
        - Date order of transactions
        - Sales of non-existing or insufficient securities
    - Writing of reconciled sales to an output file (with write_sales_file())
        - Erroneous transactions are reported and ignored in the output
        - Sales which span multiple buy lots are split out as multiple sales
          each with their own cost basis and long-term/short-term designation

    Experimental functionality:
    - There currently exists a number of methods which add support for interactive addition
      of transactions such as through a command-line-interface. This includes features such
      as undoing a transaction or detecting erroneous sales which are rolled back and ignored.
    '''

    def __init__(self,input_file_name:str,output_file_name:str='sales.txt'):
        self._i_file_name = input_file_name
        self._o_file_name = output_file_name
        self._buy_transactions = {} # Holds all loaded/entered buy transactions
        self._history = [] # Holds a buffer of this session's transactions (for interactive sessions)
        self._sale_items = {} # Dict of dict of list of sales keyed by [brokerage][ticker]
        self._file_transactions = [] # Stores all transactions read from input file

        # We track wash sales as we process transactions because we need to adjust the
        # costs basis of future purchases. Because wash sales cross brokerage boundaries,
        # we only track these by ticker symbol. As such the dict below is keyed by ticker
        self._wash_sales = defaultdict(float) # Keyed by ticker with value being that disallowed loss
        
        self.rebuild()

    ###########################################################################
    # User Methods
    ###########################################################################
    def get_num_shares(self,brokerage:str,ticker:str)->float:
        '''
        Returns the total number of shares for ticker at a given brokerage
        '''
        if brokerage not in self._buy_transactions:
            return 0.0
        if ticker not in self._buy_transactions[brokerage]:
            return 0.0
        return sum([x.amount for x in self._buy_transactions[brokerage][ticker].data])

    def print_sales_report(self):
        '''
        Prints a report of all sales
        '''
        for brokerage in self._sale_items.keys():
            print(f'Brokerage: {brokerage}')
            for ticker in self._sale_items[brokerage].keys():
                for sale in self._sale_items[brokerage][ticker]:
                    print(f'{ticker}: {sale}')

    def print_holdings_report(self):
        '''
        Prints a report of all remaining holdings
        '''
        for brokerage in self._buy_transactions.keys():
            print(f'Brokerage: {brokerage}')
            for ticker in self._buy_transactions[brokerage].keys():
                for tr in self._buy_transactions[brokerage][ticker].data:
                    print(f'{ticker}: {tr.amount} shares')

    def write_sales_file(self):
        total_proceeds = 0.0
        net_gain = 0.0
        total_disallowed_wash = 0.0
        with open(self._o_file_name,'w') as f:
            for brokerage in self._sale_items.keys():
                f.write(f'Brokerage: {brokerage}\n')
                for ticker in self._sale_items[brokerage].keys():
                    sales_list = self._sale_items[brokerage][ticker]
                    total_proceeds += sum([x.proceeds for x in sales_list])
                    total_disallowed_wash += sum([x.disallowed_wash_amount for x in sales_list])
                    net_gain += sum([x.gain for x in sales_list])
                    for sale in sales_list:
                        f.write(f'{ticker}: {sale}\n')
            f.write(f'Total proceeds = ${total_proceeds}\n')
            f.write(f'Net gain       = ${net_gain}\n')
            f.write(f'Total of disallowed wash amounts = ${total_disallowed_wash}')


    ###########################################################################
    # Internal Methods
    ###########################################################################

    def buy(self,ticker:str,amount:int,price:float,date:Any=None,comm=0.0,brokerage=None):
        '''
        Performs a buy operation, storing the transaction in the global log and into
        the appropriate ticker FIFO
        '''
        new_tr = StockTransaction(
            tr_type='buy',
            ticker=ticker,
            amount=amount,
            price=price,
            date=date,
            comm=comm,
            brokerage=brokerage)

        self.buy_transaction(new_tr)

    def sell(self,ticker:str,amount:int,price:float,date:Any=None,comm=0.0,brokerage=None):
        '''
        Performs a sell operation, storing the transaction in the global log and into
        the appropriate ticker FIFO
        '''
        new_tr = StockTransaction(
            tr_type='sell',
            ticker=ticker,
            amount=amount,
            price=price,
            date=date,
            comm=comm,
            brokerage=brokerage)

        self.sell_transaction(new_tr)
        
    def history_add(self,transaction):
        '''
        Performs a transaction deep copy and adds it to the history buffer
        '''
        self._history.append(deepcopy(transaction))

    def history_delete_last(self):
        '''
        Deletes last item in history
        '''
        if len(self._history) > 0:
            _ = self._history.pop()

    def history_delete_all(self):
        '''
        Deletes all history
        '''
        self._history = []

    def buy_transaction(self,transaction:StockTransaction,skip_history:bool=False):
        '''
        Adds a StockTransaction object into a ticker FIFO for the specified brokerage
        '''
        if transaction.brokerage not in self._buy_transactions:
            # Create a new sub-dict for this brokerage
            self._buy_transactions[transaction.brokerage] = {}
        if transaction.ticker not in self._buy_transactions[transaction.brokerage]:
            # Create a new sub-sub-dict for this ticker
                self._buy_transactions[transaction.brokerage][transaction.ticker] = Fifo() # Create a new FIFO for this ticker

        # Check date is older than last entry for this ticker
        fifo = self._buy_transactions[transaction.brokerage][transaction.ticker]
        if len(fifo) > 0:
            d1 = date.fromisoformat(transaction.date)
            d2 = date.fromisoformat(fifo.tail.date)
            if d1<d2:
                print(f'ERROR: Tried to add an older transaction with date {transaction.date}. Last transaction date is {fifo.tail.date}')
                return

        # Add any past disallowed wash sale to additional basis
        transaction.add_basis += self._wash_sales[transaction.ticker]
        self._wash_sales[transaction.ticker] = 0.0 # Clear it out since we have consumed it

        self._buy_transactions[transaction.brokerage][transaction.ticker].push(transaction)

        if not skip_history:
            self.history_add(transaction)

    def sell_transaction(self,transaction:StockTransaction,skip_history:bool=False):
        '''
        Attempts to perform a sell operation described by the StockTransaction object
        by accessing previous buy transactions. If the sale fails, an error message
        if printed to the screen and the sale is discarded.

        Because a sale transaction may encompass many previous buy transactions, we
        generate a SaleItem object for every buy transaction in the span of the sale.
        This is necessary for example not just because of variations in cost-basis
        but also that some sales may constitute long-term gains vs short-term. As such
        there are as many SaleItem objects created as there are buys in the span of the
        sale.
        '''

        # Implementation notes:
        # =====================
        # This method behaves as a simple state-machine by applying the sale transaction to
        # relevant FIFO entries (selected by brokerage and ticker) until all shares defined in the
        # sale transaction are accounted for. Because there may be one or more buy
        # transactions that cover the sale, the main loop may have to iterate through
        # a number of entries in the FIFO

        # First do some checking
        if transaction.brokerage not in self._buy_transactions:
            raise RuntimeError(f'No data for brokerage {transaction.brokerage} found')
        if transaction.ticker not in self._buy_transactions[transaction.brokerage]:
            raise RuntimeError(f'Ticker symbol {transaction.ticker} not found in brokerage {transaction.brokerage}')

        # Check date is older than last entry for this ticker
        fifo = self._buy_transactions[transaction.brokerage][transaction.ticker]
        if len(fifo) > 0:
            d1 = date.fromisoformat(transaction.date)
            d2 = date.fromisoformat(fifo.tail.date)
            if  d1<d2 :
                print(f'ERROR: Tried to add an older transaction with date {transaction.date}. Last transaction date is {fifo.tail.date}')
                return

        if not skip_history:
            self.history_add(transaction)

        # Now we iterate through the data in the FIFO for the amount requested. Note that we
        # save off popped entries incase the sale fails. In which case we push the entries
        # back to the head of the FIFO (this is useful for interactive sessions where a
        # user may enter sale transactions into a CLI for example)
        # 
        # Since a single sale transaction can generate multiple sale items (because of multiple
        # cost basis buys), we generate SaleItem objects while performing the sale loop, but
        # we do not commit these to self._sale_items until we have successfully processed a
        # sale transaction (in case of errors)
        popped_entries = []
        sale_items = [] # A list of generated SaleItem objects for this sale transaction
                        # which is only committed to self._sale_items if a sale completes
        rem_amount = transaction.amount
        fifo = self._buy_transactions[transaction.brokerage][transaction.ticker]
        while rem_amount > 0:
            if len(fifo) == 0:
                # This is an error state because we still have remaining stock to sell, but
                # we are out of FIFO entries for this ticker. As such as we have to rewind
                # the previous FIFO pop operations and place the previously popped (if any)
                # entries in the correct order back to the front of the FIFO
                for _ in range(len(popped_entries)):
                    popped_entry = popped_entries.pop()
                    popped_entry.is_sold = False # undo the sold sate
                    fifo.push_front(popped_entry)
                rem_amount = 0
                if not skip_history:
                    self.history_delete_last()
                #raise RuntimeError(f'Insufficient funds for sale of {amount} shares of {ticker}. Sale cancelled')
                print(f'Insufficient funds for sale of {transaction.amount} shares of {transaction.ticker}. Sale cancelled')
                return

            elif fifo.head.amount > rem_amount:

                # In this state, we partially consume the FIFO head, so we need to update its
                # remaining amount
                sale_items.append(self.create_sale_item(sell_tr=transaction,buy_tr=fifo.head,amount=rem_amount))
                fifo.head.amount -= rem_amount
                rem_amount = 0

            elif fifo.head.amount == rem_amount:

                # In this state our remaining sale amount exactly consumes what is left in 
                # the current FIFO head, so we need to mark the buy as fully sold and pop
                # it from the FIFO
                fifo.head.is_sold = True
                fifo.head.amount = 0
                sale_items.append(self.create_sale_item(sell_tr=transaction,buy_tr=fifo.head,amount=rem_amount))
                popped_entries.append(fifo.pop()) 
                rem_amount = 0

            else: 
                # In this case the FIFO head does not have sufficient funds,
                # so we consume it and pop the FIFO and look for a previous buy to sell against
                # in the next iteration
                # We also create a SaleItem for this chunk of the sale because the buy profile
                # comprising of the cost-basis and acquisition date may be different than the
                # next buy transaction in the FIFO
                fifo.head.is_sold = True
                sale_items.append(self.create_sale_item(sell_tr=transaction,buy_tr=fifo.head,amount=fifo.head.amount))
                rem_amount  -= fifo.head.amount
                popped_entries.append(fifo.pop()) 

        # If we got here, the sale was successful so we need to write all generated 
        # SaleItem objects to the main dict
        for sale_item in sale_items:
            if transaction.brokerage not in self._sale_items:
                self._sale_items[transaction.brokerage] = {}
            if transaction.ticker not in self._sale_items[transaction.brokerage]:
                self._sale_items[transaction.brokerage][transaction.ticker] = []
            self._sale_items[transaction.brokerage][transaction.ticker].append(sale_item)

    def create_sale_item(self,sell_tr:StockTransaction,buy_tr:StockTransaction,amount:float)->SaleItem:
        '''
        Generates and returns a SaleItem object based on a sell and buy transaction and 
        the number of shares (amount) being sold at this iteration
        Modifies the sell transaction in the case of a wash sale by updating the relevant
        wash-sale fields
        '''
        # The cost-basis must take into account any previous wash sale disallowed amounts
        # that have not been cleared out.
        cost_basis = buy_tr.add_basis + (buy_tr.price * amount) # FIXME, need to add the brokerage fees/commission
        sale_item = (
            SaleItem(
                brokerage=sell_tr.brokerage,
                ticker=sell_tr.ticker,
                sale_price=sell_tr.price,
                amount=amount,
                date_acquired=buy_tr.date,
                date_sold=sell_tr.date,
                cost_basis=cost_basis)
        )
        # Check if there is a wash sale trigger.
        # NOTE: The lot which is at the head of the FIFO cannot constitute the wash
        #       sale trigger. Only buys following (newer) than the FIFO head can
        #       be considered to counted to establish a "pre-buy" wash sale scenario
        wash_transaction = self.find_wash_trigger(sell_tr) 
        if wash_transaction and wash_transaction != buy_tr: # Filter out the head transaction
            if sale_item.gain < 0:
                sale_item.wash = True
                # If the pre-buy or post-buy is a share amount smaller than the amount of shares in this
                # sale, we only "wash" the amount of shares bought, not the complete sale. This is why
                # we have the "min" term.
                sale_item.disallowed_wash_amount = abs(sale_item.gain_per_share * (min(amount,wash_transaction.amount)))
                self._wash_sales[sell_tr.ticker] = sale_item.disallowed_wash_amount
        
        return sale_item

    def undo(self):
        '''
        Undoes the last addition or sale. This requires re-building the entire stock data
        state from the last file state and the current session buffer sans the last 
        operation
        '''
        
        if len(self._history) > 0:
            self.history_delete_last()
            self.rebuild() # Re-build from data file
            for tr in self._history:
                # Re-play the current history buffer, but do not 
                # add these to the history as this would be double-adding
                if tr.tr_type == 'buy':
                    self.buy_transaction(tr,skip_history=True)
                else:
                    self.sell_transaction(tr,skip_history=True)
        else:
            print('Nothing to undo from this session')

    def rebuild(self,file_name=None,clear_history=False):
        '''
        Re-builds this object based on the associated file name. Optionally a
        different file name can be specified from which to re-build the
        data
        '''
        if file_name:
            fname = file_name
        else:
            fname = self._i_file_name

        if not os.path.exists(fname):
            print(f'Data file {fname} not found')
            return

        if clear_history:
            self.history_delete_all()

        # Remove all transactions
        self._buy_transactions = {}

        # First we pre-read the entire file so we can store all transactions
        # for wash-sale analysis which requires looking at "future" transactions
        with open(fname,'r') as f:
            for line in f:
                 if line.startswith('{'):
                    tr = StockTransaction.from_dict(json.loads(line))
                    self._file_transactions.append(tr)

        for tr in self._file_transactions:
            # When we perform the re-build, we do not add these transactions to the current
            # session history to avoid these being re-written upon a flush
            if tr.tr_type == 'buy':
                self.buy_transaction(tr,skip_history=True)
            else:
                self.sell_transaction(tr,skip_history=True)

    def flush_to_file(self,file_name=None):
        '''
        Writes the current session trade history to the associated file name. Optionally
        a different file name can be specified
        '''
        if file_name:
            fname = file_name
        else:
            fname = self._i_file_name
        with open(fname,'a') as f:
            print(f'Writing stock data to file {fname}')
            for tr in self._history:
                f.write(json.dumps(tr.asdict())+'\n')

    def find_wash_trigger(self,transaction:StockTransaction)->StockTransaction:
        '''
        Attempts to find a candidate pre-buy or post-buy transaction in a window
        defined by +/-30-days of the transaction sale date.
        Buys which occurred 30-days prior and have been 
        fully disposed off are not considered as wash triggers. All future
        purchases within a +30-day window are however by definition wash
        buys

        If a wash buy trigger candidate is found, the potentially offending transaction 
        is returned otherwise None is returned
        '''
        # We search the stored transactions for a match of a buy which is not
        # already sold
        d = date.fromisoformat(transaction.date)
        d_plus_30 = d + timedelta(days=30)
        d_minus_30 = d - timedelta(days=30)

        for tr in self._file_transactions:
            tr_date = date.fromisoformat(tr.date)
            if tr.tr_type == 'buy' and tr_date >= d_minus_30 and tr_date <= d_plus_30 and not tr.is_sold:
                #print(f'INFO: Wash Sale detected for {transaction.ticker} with sale date {transaction.date} with wash trigger by on {tr.date}')
                return tr
        return None