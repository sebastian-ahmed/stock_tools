# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

import argparse

def proc_cla(iparser:argparse.ArgumentParser=None,descr:str='')->argparse.ArgumentParser:
    '''
    Process command line arguments and return a parser object. Optionally take in
    an existing argparse object and add parser options to it.
    '''
    if iparser:
        assert isinstance(iparser,argparse.ArgumentParser), "Object is not an argument parser"
        parser = iparser
    else:
        # Create a new object if one is not specified
        parser = argparse.ArgumentParser(description=descr)
    
    parser.add_argument('--infile',     metavar='<stock transaction file>', type=str,  help='Specifies the file which contains stock transactions. Supported formats are .csv and .json')
    parser.add_argument('--outfile',    metavar='<output report file>',     type=str,  help='Optionally specifies an output file base-name for the reports')
    parser.add_argument('--date_start', metavar='<YYYY-MM-DD>',             type=str,  help='Optionally specifies a start date for report generation. If not specified, the date of the first transaction is used')
    parser.add_argument('--date_end',   metavar='<YYYY-MM-DD>',             type=str,  help='Optionally specifies an end date for report generation. If not specified, the date of the last transaction is used')
    parser.add_argument('--fetch_quotes', action='store_true',                         help='Includes current values based on current stock prices. Note: This causes a slow-down in report generation due to web API calls')
    parser.add_argument('--expanded',     action='store_true',                         help='Output holdings report will create a line item for each independent buy lot instead of summing all lots per ticker')
    parser.add_argument('--debug',        action='store_true',                         help='Enables debug-level logging messages in the run log file and console output')
    
    return parser.parse_args()