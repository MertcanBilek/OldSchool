import threading as th

class _Indexer:
    def __init__(self, name = None):
        self.name = name
        self._list = []
    
    def add(self,o):
        self._list.insert(0,o)


    def pop(self):
        while True:
            try:
                o = self._list.pop()
                break
            except IndexError:
                pass
        return o

def _thread(func, *args, daemon = True, **kwargs):
    t = th.Thread(target=func, args=args, kwargs=kwargs)
    t.daemon = daemon
    t.start()

if __name__ == "__main__":
    import time
    i = _Indexer()
    def c(i):
        time.sleep(2)
        i.add("100")
        i.add(229)
    _thread(c,i)
    print("Waiting")
    a = i.pop()
    b = i.pop()
    print(a,b)