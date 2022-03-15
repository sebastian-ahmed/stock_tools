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
    parser.add_argument('--outfile',    metavar='<output report file>',     type=str,  help='Optionally specifies an output file for the report')
    parser.add_argument('--date_start', metavar='<YYYY-MM-DD>',             type=str,  help='Optionally specifies a start date for report generation. If not specified, the date of the first transaction is used')
    parser.add_argument('--date_end',   metavar='<YYYY-MM-DD>',             type=str,  help='Optionally specifies an end date for report generation. If not specified, the date of the last transaction is used')
    #parser.add_argument('--holdings',   action='store_true',                           help='Include resulting holdings in report')
    
    return parser.parse_args()