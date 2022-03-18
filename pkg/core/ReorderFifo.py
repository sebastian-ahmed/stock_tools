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
    # from the Fifo base class but also composes a Fifo base class object, so in a
    # sense it is composing and inheriting at the same time. The inheritance 
    # achieves re-use of the interface semantics and the composition achieves
    # the ability to add the re-ordering layer with a proxy FIFO data element 
    # whilst allowing manipulation of the underlying Fifo object. We can
    # manipulate the underlying object by calling the base class interface.

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
        self._data.append(elem)
        super().push(elem)

    def push_front(self,elem):
        '''
        Pushes an object to the head (front) of the FIFO
        '''
        self._data.insert(0,elem)
        super().push_front(elem)

    def pop(self):
        '''
        Removes the object at the head of the FIFO and returns it
        '''
        # First we remove the equivalent element from our wrapped Fifo
        # object before popping our proxy entry
        self.fifo._data.remove(self.head)
        return self._data.pop(0)
