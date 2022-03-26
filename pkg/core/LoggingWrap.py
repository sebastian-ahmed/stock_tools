import logging

'''
Wrapper functions for built-in python logging calls which allows log messages
to also be output to the console. Although built-in logging provides the
StreamHandler class, messages passed through such a stream only contain the
message string which means that the log-level information cannot be printed
to the screen.

Messages which are printed to the console follow the set logging level
'''

def log_debug(msg:str):
    logging.debug(msg)
    if logging.root.level <= logging.DEBUG:
        print('DEBUG: ' + msg)

def log_info(msg:str):
    logging.info(msg)
    if logging.root.level <= logging.INFO:
        print('INFO: ' + msg)

def log_warn(msg:str):
    logging.warn(msg)
    if logging.root.level <= logging.WARN:
        print('WARNING: ' + msg)

def log_error(msg:str):
    logging.error(msg)
    if logging.root.level <= logging.ERROR:
        print('ERROR: ' + msg)