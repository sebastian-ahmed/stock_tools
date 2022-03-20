import yfinance as yf
from prettytable import PrettyTable

import json
import csv
import os.path
from copy import deepcopy
from datetime import date,timedelta
from typing import Any, Tuple
from collections import defaultdict

from pkg.core.StockTransaction import StockTransaction
from pkg.core.TransactionCommands import Command_SPLIT
from pkg.core.SaleItem import SaleItem
from pkg.core.Fifo import Fifo
from pkg.core.ReorderFifo import ReorderFifo

class StockTransactor:
    '''
    Implements the processing layer of stock transactions. An object of this class is 
    responsible for the following operations:
    - Reading in of a stock transaction data file (using either CSV or JSON formats)
    - Processing all transactions in the file
    - Matching sales relative to previous purchases using either the
      First-in-first-out (FIFO) default ordering or ordering with specified buy lots
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

    @property
    def current_holdings(self)->dict:
        '''
        Returns a dict of current holdings organized as a dict of dicts of list values
        {<brokerage>:
                     {<ticker>: [StockTransaction]
        
        In order to access all buy transaction holdings for brokerage B for tickert T:
        transactions = st.current_holdings['B']['T']

        (where st is a StockTransactor object and transactions is list of StockTransaction
        objects)

        The ordering of transaction objects is such that transactions[0] would be the oldest
        buy transaction
        '''
        return self._buy_transactions

    @property
    def sales(self)->dict:
        '''
        Returns a dict of all sales organized as a dict of dicts of list values
        {<brokerage>:
                     {<ticker>: [SaleItem]

        In order to access all sale items for brokerage B for tickert T:
        sale_items = st.current_holdings['B']['T']

        (where st is a StockTransactor object and transactions is list of SaleItem
        objects)

        The ordering of sale items is such that sale_items[0] would be the oldest
        sale
        ''' 
        return self._sale_items

    def __init__(self,input_file_name:str,output_file_name:str='sales.txt'):
        self._i_file_name = input_file_name
        if output_file_name == None: # Required if name passed through an argparse object
            output_file_name = 'sales.txt'
        self._o_file_name = output_file_name
        self._buy_transactions = {} # Holds all loaded/entered buy transactions, keyed by brokerage
        self._history = [] # Holds a buffer of this session's transactions (for interactive sessions)
        self._sale_items = {} # Dict of dict of list of sales keyed by [brokerage][ticker]
        self._file_transactions = [] # Stores all transactions read from input file
        self._splits = {} # Sequential list of SPLIT commands

        # We track wash sales as we process transactions because we need to adjust the
        # costs basis of future purchases. Because wash sales cross brokerage boundaries,
        # we only track these by ticker symbol. As such the dict below is keyed by ticker
        self._wash_sales = defaultdict(float) # Keyed by ticker with value being that disallowed loss
        
        self.rebuild()

    ###########################################################################
    # User Methods
    ###########################################################################
    def get_num_shares(self,ticker:str,brokerage:str=None)->float:
        '''
        Returns the total number of shares for ticker at a given brokerage. If
        brokerage is not specified, the total shares across all brokerages are
        returned.
        '''
        if brokerage:
            if brokerage not in self._buy_transactions:
                return 0.0
            if ticker not in self._buy_transactions[brokerage]:
                return 0.0
            return sum([x.amount for x in self._buy_transactions[brokerage][ticker].data])
        else:
            val = 0.0
            for b in self._buy_transactions.keys():
                if ticker in self._buy_transactions[b]:
                    val += sum([x.amount for x in self._buy_transactions[b][ticker].data])
            return val

    def print_report(self,date_range:Tuple[str,str]=None,fetch_quotes=False):
        '''
        Prints a report of sales and resulting holdings.
        When no date_range is specified,
        writes all sales, otherwise writes sales in the specified range.
        When specifying a date range, a tuple of ISO format string dates must
        be provided in the format:
        date_range = ('YYYY-MM-DD','YYYY-MM-DD')

        For example, to report all sales in the year 2022, specify:
        date_range = ('2022-01-01','2022-12,31')

        If the date range is negative a RuntimeError will be raised

        Setting fetch_quotes=True will add current values for
        the holdings section of the report. This requires an internet
        connection and can cause delays in report generation
        '''
        print(self.sales_report_str(date_range))
        print(self.holdings_report_str(fetch_quotes))


    def write_report(self,date_range:Tuple[str,str]=None,fetch_quotes=False):
        '''
        Writes report of sales and resulting holdings to report file.
        When no date_range is specified,
        writes all sales, otherwise writes sales in the specified range.
        When specifying a date range, a tuple of ISO format string dates must
        be provided in the format:
        date_range = ('YYYY-MM-DD','YYYY-MM-DD')

        For example, to report all sales in the year 2022, specify:
        date_range = ('2022-01-01','2022-12,31')

        If the date range is negative a RuntimeError will be raised

        Setting fetch_quotes=True will add current values for
        the holdings section of the report. This requires an internet
        connection and can cause delays in report generation
        '''
        with open(self._o_file_name,'w') as f:
            f.write(self.sales_report_str(date_range))
            f.write(self.holdings_report_str(fetch_quotes))

    ###########################################################################
    # Internal Methods
    ###########################################################################

    def sales_report_str(self,date_range:Tuple[str,str]=None)->str:
        '''
        Returns the sales report string for printing to screen or file
        '''
        ostr = self.banner_wrap_str('SALES REPORT',level=0)

        if date_range:
            if date_range[0]:
                d1 = date.fromisoformat(date_range[0])
            else:
                d1 = None
            if date_range[1]:
                d2 = date.fromisoformat(date_range[1])
            else:
                d2 = None
            if d2 and d1 and d2 < d1:
                raise RuntimeError(f'Specified a negative date range: from {d1} to {d2}')
            ostr += f'Date range: {d1} to {d2}\n'

        total_proceeds = 0.0
        net_gain = 0.0
        total_disallowed_wash = 0.0
        sales_list = []
        table = PrettyTable()
        table.field_names = SaleItem.fields_list()

        for brokerage in self._sale_items.keys():
            #ostr += f'\nBrokerage: {brokerage}'
            for ticker in self._sale_items[brokerage].keys():
                if date_range: # Sales in a date-range
                    if d1 and d2:
                        sales_list = [
                            x for x in self._sale_items[brokerage][ticker] 
                            if
                            date.fromisoformat(x.date_sold) >= d1 and 
                            date.fromisoformat(x.date_sold) <= d2
                            ]
                    elif d1 and not d2:
                        sales_list = [
                            x for x in self._sale_items[brokerage][ticker] 
                            if
                            date.fromisoformat(x.date_sold) >= d1
                            ]
                    elif d2 and not d1:
                        sales_list = [
                            x for x in self._sale_items[brokerage][ticker] 
                            if
                            date.fromisoformat(x.date_sold) <= d2
                            ]
                    else: # All sales
                        # This case can occur when the date_range tuple is passed
                        # in with value (None,None)
                        sales_list = [
                            x for x in self._sale_items[brokerage][ticker] 
                            ]
                else: # All sales (when date_range is None)
                    sales_list = self._sale_items[brokerage][ticker]
                total_proceeds += sum([x.net_proceeds for x in sales_list])
                total_disallowed_wash += sum([x.dis_wash_loss for x in sales_list])
                net_gain += sum([x.gain for x in sales_list])
                if len(sales_list) == 0:
                    ostr += 'No sales were found given the criteria\n'
                    continue
                for sale in sales_list:
                    values_list = []
                    for x in SaleItem.fields_list():
                        attr_val = getattr(sale,x)
                        if isinstance(attr_val,float):
                            values_list.append(round(attr_val,2))
                        else:
                            values_list.append(attr_val)
                    table.add_row(values_list)
        if len(sales_list)>0:
            ostr += '\n' + str(table) + '\n'
            ostr += f'\nTotal proceeds                = ${total_proceeds}\n'
            ostr += f'Net gain (raw)                = ${net_gain}\n'
            ostr += f'Net gain (adjusted)           = ${round(net_gain+total_disallowed_wash,2)}\n'
            ostr += f'Total disallowed wash amounts = ${round(total_disallowed_wash,2)}\n'
        else:
            ostr += '*** There were no sales in the specified date range ***\n'

        return ostr

    def holdings_report_str(self,fetch_quotes=False):
        '''
        Returns the current holdings report string
        '''
        ostr = self.banner_wrap_str('HOLDINGS REPORT',level=0)
        for brokerage in self._buy_transactions.keys():
            total_value = 0.
            total_cost_basis = 0.0
            net_gain = 0.
            ostr += f'\nBrokerage: {brokerage}'
            table = PrettyTable()
            if fetch_quotes:
                table.field_names = [
                    'ticker',
                    'amount',
                    'cost-basis',
                    'added-basis',
                    'cur-price',
                    'cur-value',
                    'cur-gain',
                    'cur-adjusted-gain']
            else:
                table.field_names = [
                    'ticker',
                    'amount',
                    'cost-basis',
                    'added-basis']
            for ticker in self._buy_transactions[brokerage].keys():
                if fetch_quotes: # Grab current stock price data from web
                    yticker = yf.Ticker(ticker.upper())
                    current_price = yticker.info["regularMarketPrice"]
                for tr in self._buy_transactions[brokerage][ticker].data:
                    cost_basis = tr.price * tr.amount + tr.add_basis
                    if fetch_quotes:
                        current_value = current_price * tr.amount
                        current_gain  = tr.amount*(current_price-tr.price)
                        current_gain_pct = round(100* current_gain/cost_basis,2)
                        current_adjusted_gain = current_gain - tr.add_basis
                        current_adjusted_gain_pct = round(100*current_adjusted_gain/cost_basis,2)
                        table.add_row([
                            ticker,
                            tr.amount,
                            round(cost_basis,2),
                            round(tr.add_basis,2),
                            current_price,
                            round(current_value,2),
                            f'{round(current_gain,2)} ({current_gain_pct}%)',
                            f'{round(current_adjusted_gain,2)} ({current_adjusted_gain_pct}%)'])
                        total_cost_basis += cost_basis
                        total_value += current_value
                    else:
                        table.add_row([ticker,tr.amount,round(cost_basis,2),round(tr.add_basis,2)])
                    ostr += '\n'
            ostr += table.get_string() + '\n'
            if fetch_quotes:
                net_gain = total_value - total_cost_basis
                net_gain_percent = 100*net_gain/(total_cost_basis)
                ostr += f'Total Value         = ${round(total_value,2)}\n'
                ostr += f'Total Adjusted Gain = ${round(net_gain,2)} ({round(net_gain_percent,2)}%)\n'
        return ostr

    def buy(self,brokerage:str,ticker:str,amount:int,price:float,date:Any=None,comm=0.0):
        '''
        Performs a buy operation
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

    def sell(self,brokerage:str,ticker:str,amount:int,price:float,date:Any=None,comm=0.0):
        '''
        Performs a sell operation
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
        if transaction.brokerage is None or transaction.brokerage == '':
            raise RuntimeError(f'Invalid brokerage value {transaction.brokerage}')
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
        #
        # There are two possible FIFO views (as defined by the variable fifo)
        # 1) The default FIFO object built up by buy transactions which reflects the 
        #    chronological first-in-first-out buy ordering
        # 2) An alternative "proxy" FIFO which is adds a re-ordering layer to the
        #    default FIFO to match an explicit sale schedule (i.e., when the sale
        #    defines the selling of specific buy lots)

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

        # First we determine if this sell transaction has a default FIFO sequence or
        # if it specifies custom lots. If custom lots are specified, the relevant
        # FIFO object (for the specified ticker) is accessed directly by identifying
        # individual lots and transacting upon those in the specified order. Upon
        # exhausting a specific lot, the entry is popped broad-side. This is achieved by
        # wrapping the FIFO object and virtualizing the pop operations
        base_fifo = self._buy_transactions[transaction.brokerage][transaction.ticker]

        if len(transaction.lot_ids) > 0:
            fifo = ReorderFifo(base_fifo,transaction.lot_ids,transaction.ticker)
        else:
            fifo = base_fifo

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
                raise RuntimeError(f'Insufficient funds for sale of {transaction.amount} shares of {transaction.ticker}. Sale cancelled')
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
                sale_items.append(self.create_sale_item(sell_tr=transaction,buy_tr=fifo.head,amount=rem_amount,last=True))
                popped_entries.append(fifo.pop()) 
                rem_amount = 0

            else: 
                # In this case the FIFO head does not have sufficient funds,
                # so we consume it and pop the FIFO and look for a subsequent buy to sell against
                # in the next iteration
                # We also create a SaleItem for this chunk of the sale because the buy profile
                # comprising of the cost-basis and acquisition date may be different than the
                # next buy transaction in the FIFO
                fifo.head.is_sold = True
                sale_items.append(self.create_sale_item(sell_tr=transaction,buy_tr=fifo.head,amount=fifo.head.amount,last=True))
                rem_amount  -= fifo.head.amount
                popped_entries.append(fifo.pop()) 

        # If we got here, the sale was successful so we need to write all generated 
        # SaleItem objects to the main dict

        # We apply the sales transaction object commission to the first SaleItem
        # object.
        sale_items[0].comm = transaction.comm

        for sale_item in sale_items:
            if transaction.brokerage not in self._sale_items:
                self._sale_items[transaction.brokerage] = {}
            if transaction.ticker not in self._sale_items[transaction.brokerage]:
                self._sale_items[transaction.brokerage][transaction.ticker] = []
            self._sale_items[transaction.brokerage][transaction.ticker].append(sale_item)

        

    def create_sale_item(self,sell_tr:StockTransaction,buy_tr:StockTransaction,amount:float,last=False)->SaleItem:
        '''
        Generates and returns a SaleItem object based on a sell and buy transaction and 
        the number of shares (amount) being sold at this iteration
        Modifies the sell transaction in the case of a wash sale by updating the relevant
        wash-sale fields
        The last field indicates that this sale constitutes the remainder or entirety of 
        the buy transaction. When this is True, we also apply the buy transaction commission
        to the cost-basis
        '''
        # The cost-basis must take into account any previous wash sale disallowed amounts
        # that have not been cleared out. The commission of a fully consumed buy transaction 
        # is also added to the costs basis
        cost_basis = buy_tr.add_basis + (buy_tr.price * amount)
        if last:
            cost_basis += buy_tr.comm

        sale_item = (
            SaleItem(
                brokerage=sell_tr.brokerage,
                ticker=sell_tr.ticker,
                sale_price=sell_tr.price,
                amount=amount,
                date_acquired=buy_tr.date,
                date_sold=sell_tr.date,
                cost_basis=cost_basis,
                lot_id=buy_tr.lot_id)
        )
        # Check if there is a wash sale trigger.
        # NOTE: The lot which is at the head of the FIFO cannot constitute the wash
        #       sale trigger. Only buys newer than the FIFO head can
        #       be considered for establishing a "pre-buy" wash sale scenario
        wash_transaction = self.find_wash_trigger(sell_tr) 
        if wash_transaction and wash_transaction != buy_tr: # Filter out the head transaction
            if sale_item.gain < 0:
                sale_item.wash = True
                print(f'INFO: Wash Sale detected for {sell_tr.ticker} with sale date {sell_tr.date} with wash trigger buy on {wash_transaction.date}')

                # If the pre-buy or post-buy is a share amount smaller than the amount of shares in this
                # sale, we only "wash" the amount of shares bought, not the complete sale. This is why
                # we have the "min" term.
                sale_item.dis_wash_loss = abs(sale_item.gain_per_share * (min(amount,wash_transaction.amount)))
                self._wash_sales[sell_tr.ticker] = sale_item.dis_wash_loss
        
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
        
        fformat = None
        if fname.endswith('.csv'): # CSV file
            print(f'Reading file {fname} as CSV')
            fformat = 'csv'
        elif fname.endswith('.json'): # JSON file
            print(f'Reading file {fname} as JSON')
            fformat = 'json'
        
        with open(fname,'r') as f:
            if fformat == 'json':
                for line in f:
                    if line.startswith('{'):
                        dict_line = json.loads(line)
                        if list(dict_line.keys())[0] == 'cmd': # special command
                            self.process_command(dict_line['cmd'])
                        else:
                            tr = StockTransaction.from_dict(dict_line)
                            self._file_transactions.append(tr)
            elif fformat == 'csv':
                csv.register_dialect('stocks', delimiter=',', skipinitialspace=True)
                reader = csv.DictReader(f,dialect='stocks')
                for line in reader:
                        if line['ticker'].startswith('!'): # Special instruction:
                            self.process_command(line['ticker'])
                        else:
                            tr = StockTransaction.from_dict(line)
                            self._file_transactions.append(tr)
            else:
                raise RuntimeError(f'File {fname} is not a supported input format')

        # Apply amount and price adjustments for any stock splits defined in
        # the input file
        self.split_stocks()

        for tr in self._file_transactions:
            # When we perform the re-build, we do not add these transactions to the current
            # session history to avoid these being re-written upon a flush
            if tr.tr_type == 'buy':
                self.buy_transaction(tr,skip_history=True)
            else:
                self.sell_transaction(tr,skip_history=True)

    def process_command(self,cmd_str:str):
        '''
        Processes command entries in stock transaction input file. Expected formats
        of commands are '#<COMMAND>#Argument1#Argument2#Argument3...'
        '''
        cmd_full = cmd_str[1:].split('#') # Remove the '!' char at start of string
        cmd_word = cmd_full[0]
        cmd_args = cmd_full[1:]

        print(f'INFO: Encountered command: {cmd_word} with arguments {cmd_args}')

        if cmd_word == 'SPLIT':
            # arg format: ticker,split_amount,date
            if len(cmd_args) != 3:
                raise RuntimeError(f'Invalid number of arguments specified for SPLIT command. Expected 3, but got {len(cmd_args)}')
            ticker = cmd_args[0]
            if ticker not in self._splits:
                self._splits[ticker] = []
            self._splits[cmd_args[0]].append(Command_SPLIT(ticker=ticker,amount=float(cmd_args[1]),date=cmd_args[2]))
        else:
            raise RuntimeError(f'Unsupported special command: {cmd_word}')

    def split_stocks(self):
        '''
        Iterates through stock buy lots and performs split operations as defined in 
        the self._splits dict. This involves changing the amount field and price per
        share while maintaining a constant cost basis.
        '''
        # Order stock split information by date field
        for ticker in self._splits:
            self._splits[ticker] = sorted(self._splits[ticker],key=lambda x:date.fromisoformat(x.date))

        # Because there can be multiple stock splits and un-splits over time
        # our outer iteration is the stock splits ordered by date. This means we
        # must perform multiple passes through the _file_transactions list to 
        # update on a split by split basis. For example, if there are two splits, one on
        # date-A and one on date-B (where date-B > date-A), is there is a buy lot of
        # that stock occuring before date-A, then it will be split twice over two passes
        for ticker in self._splits:
            for split in self._splits[ticker]:
                for tr in [
                    x for x in self._file_transactions 
                    if x.tr_type=='buy' and 
                    x.ticker==ticker and
                    date.fromisoformat(x.date) <= date.fromisoformat(split.date)
                    ]:
                    tr.amount = tr.amount * split.amount  # scale the amount by split amount
                    tr.price  = tr.price / split.amount   # scale the per-share price by split amount
                    
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
                return tr
        return None

    def banner_wrap_str(self,heading:str,level:int=0)->str:
        '''
        Returns the input string wrapped with a banner with level-0 or level-1
        with level-0 being the biggest banner 
        '''
        ostr = ''
        if level < 1:
            ostr += '='*80 + '\n'
            ostr += '=' + ' '*self.get_banner_margins(80,len(heading))[0]
            ostr += heading + ' '*self.get_banner_margins(80,len(heading))[1] + '=\n'
            ostr += '='*80 + '\n'
        else:
            ostr += ' '*20 + '='*40 + '\n'
            ostr += ' '*20 + '=' + ' '*self.get_banner_margins(40,len(heading))[0]
            ostr += heading + ' '*self.get_banner_margins(40,len(heading))[1] + '=\n'
            ostr += ' '*20 + '='*40 + '\n'
        return ostr

    def get_banner_margins(self,banner_len:int,heading_len:int)->Tuple[int,int]:
        '''
        Given a heading, returns the left and right margin white-space amounts for
        a banner of length banner_len. Returns a tuple of ints (left-gap,right-gap)
        Assumes that the left and right extremes of the heading part of the banner
        consume one character each. If the heading_len cannot fit into the banner_len
        (0,0) is returned
        '''
        total_ws = banner_len - heading_len - 2
        right_ws = max(0,int(total_ws/2))
        left_ws  = max(0,total_ws - right_ws)
        return left_ws,right_ws