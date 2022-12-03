# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

from abc import abstractmethod

class Command:
    '''
    Non-concrete base class for defining special processing commands.
    Each command should inherit from this base class using the class naming
    schema Command_<COMMAND-NAME>

    Each specialization should override __init__ to process the list
    of commands passed in by the command parser and call the base
    __init__ method before the override implementation
    '''
    subclass_prefix = 'Command_'

    @abstractmethod
    def __init__(self,cmd_args:list):
        '''
        Defines initialization interface. Must be overridden and
        called first before sub-class initialization code
        '''

    @classmethod
    def command_name(cls):
        '''
        Returns this command's string name
        '''
        return cls.__name__[len(Command.subclass_prefix):] 

    @classmethod
    def supported_commands(cls)->list:
        '''
        Returns a list of strings of supported commands. This method
        should only be called from the base class
        '''
        return [x.command_name() for x in cls.__subclasses__()]


class Command_SPLIT(Command):
    def __init__(self,cmd_args:list,*args,**kwargs):
        super().__init__(cmd_args,*args,**kwargs)
        # arg format: ticker,split_amount,date
        if len(cmd_args) != 3:
            raise RuntimeError(f'Invalid number of arguments for {self.command_name()} command. Expected 3, but got {len(cmd_args)}')

        self.ticker = cmd_args[0]
        self.amount = float(cmd_args[1])
        self.date   = cmd_args[2]

class Command_LIQUIDATE(Command):
    '''
    Models the global liquidation of a security which affects all buy lots in all brokerages for specified
    security. The payout_per_share field allows specifying any remaining payouts for the security
    '''
    def __init__(self,cmd_args:list,*args,**kwargs):
        super().__init__(cmd_args,*args,**kwargs)
        # arg format: ticker,payout_per_share,date
        if len(cmd_args) != 3:
            raise RuntimeError(f'Invalid number of arguments for {self.command_name()} command. Expected 3, but got {len(cmd_args)}')

        self.ticker = cmd_args[0]
        self.payout_per_share = float(cmd_args[1])
        self.date   = cmd_args[2]

class Command_WASHGROUP(Command):

    def __init__(self,cmd_args:list,*args,**kwargs):
        '''
        tickers is a list containing ticker strings which
        define a wash-sale group. Performs some basic
        checking that each item is a string type
        '''
        super().__init__(cmd_args,*args,**kwargs)
        for ticker in cmd_args:
            if not isinstance(ticker,str):
                raise TypeError(f'WASHGROUP ticker {ticker} is not a string')
        self._tickers = cmd_args

    def matches(self,ticker:str)->list:
        '''
        Returns a list of tickers which are in the wash-group
        of ticker. If there are no matches, an empty list is 
        returned
        '''
        rlist = []
        if ticker in self._tickers:
            rlist = [x for x in self._tickers if x != ticker]
        return rlist