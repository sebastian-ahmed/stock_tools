# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

from pkg.core.Fifo import Fifo

class ReorderFifo(Fifo):
    '''
    Implements a wrapping layer around FIFO to present the FIFO with a re-ordered
    subset of elements to enable a custom lot sale schedule.
    This allows usage of an existing ordered FIFO where specific elements (of another
    defined sequence order) appear to be organized sequentially in the FIFO.
    The wrapping layer performs the mapping of the virtual FIFO to the actual FIFO,
    so when the head of the proxy Fifo is popped, the equivalent entry in the wrapped
    Fifo is also popped.

    Because ReorderFifo inherits from Fifo, it supports the same interface methods 
    '''

    # Implementation notes:
    # Here I use a bit of an interesting association pattern. The ReorderFifo inherits
    # from the Fifo base class but also aggregates a Fifo base class object, so in a
    # sense it is aggregating and inheriting at the same time. The inheritance 
    # achieves re-use of the interface semantics and the aggregation achieves
    # the ability to add the re-ordering layer with a proxy FIFO data element 
    # whilst allowing manipulation of the underlying Fifo object in tandem
    # Apparently this is a variation of the "proxy pattern". The only difference
    # here is that this object receives a reference of the object it is proxying
    # as opposed to composing it.

    def __init__(self,fifo:Fifo,lot_ids:list,ticker:str,*args,**kwargs):
        '''
        fifo    : Specifies the Fifo object to be wrapped
        lot_ids : Specifies the ordered list of lot ids
                  which form the virtual FIFO sequence
        '''
        super().__init__(*args,**kwargs)
        # Analyze the Fifo object and build the virtualized
        # view of data based on the specified element ordering
        self._data = [] # We override the data element
        self.fifo = fifo
        found_ids = 0
        for id in lot_ids:
            for element in self.fifo.data:
                if element.lot_id == id:
                    self._data.append(element)
                    found_ids += 1
        if found_ids < len(lot_ids):
            raise RuntimeError(f'Unable to find all specified lot_ids {lot_ids} for ticker {ticker}')

    def push(self,elem):
        '''
        Pushes an object into the tail (end) of the FIFO
        '''
        self.fifo.push(elem) # wrapped FIFO push
        super().push(elem) # proxy FIFO push

    def push_front(self,elem):
        '''
        Pushes an object to the head (front) of the FIFO
        '''
        self.fifo.push_front(elem) # wrapped FIFO push_front
        super().push_front(elem) # proxy FIFO push_front

    def pop(self):
        '''
        Removes the object at the head of the FIFO and returns it
        '''
        # First we remove the equivalent element from our wrapped Fifo
        # object before popping our proxy entry
        self.fifo._data.remove(self.head)
        return self._data.pop(0)
