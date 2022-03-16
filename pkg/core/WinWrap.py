# Copyright 2021 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

import os

class WinWrap(object):
    '''
    Context management class to wrap functions with a wait for ENTER step
    when running on Windows systems. This is needed when a main script
    is called directly as an executable
    '''
    def __init__(self,fHandle):
        self._fHandle = fHandle

    def __call__(self):
        self._fHandle()

    def __enter__(self):
        return self

    def __exit__(self,*args):
        if os.name == 'nt':
            #input("\nPress ENTER to exit")
            pass