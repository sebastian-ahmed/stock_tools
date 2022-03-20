# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

class Fifo:
    '''
    Implements a simple first-in-first-out sequence class with FIFO semantics
    '''

    def __init__(self):
        self._data = []

    @property
    def head(self):
        '''
        Returns the object at the head of the FIFO. If empty, returns None
        '''
        if len(self._data) > 0:
            return self._data[0]
        return None

    @property
    def tail(self):
        '''
        Returns the object at the tail of the FIFO. If empty, returns None
        '''
        if len(self._data) > 0:
            return self._data[-1]
        return None

    @property
    def data(self)->list:
        '''
        Returns a list representing the data storage element of the FIFO.
        Entry at index-0 represents the head of the FIFO
        '''
        return self._data

    def push(self,elem):
        '''
        Pushes an object into the tail (end) of the FIFO
        '''
        self._data.append(elem)

    def push_front(self,elem):
        '''
        Pushes an object to the head (front) of the FIFO
        '''
        self._data.insert(0,elem)

    def pop(self):
        '''
        Removes the object at the head of the FIFO and returns it
        '''
        return self._data.pop(0)

    def __len__(self):
        return len(self._data)