# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

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