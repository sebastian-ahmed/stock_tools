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