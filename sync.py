import asyncio
from watchdog import events, observers

class TextObjectObserver(ABC):
    def on_textobject_removed(self, textobject, typ, path):
        pass

    def on_textobject_moved(self, textobject, previous_span, typ, path):
        pass

    def on_textobject_added(self, textobject, typ, path):
        pass

def sync(*textobjectstorage: TextObjectStorage):
    """create a Context Manager which handles syncronization"""
    return TextObjectStorageSyncronization(*textobjectstorage)

def watch(*textobjectstores: TextObjectStorage):
    """start a co-routine to watch the files assocated to 
    the :obj:`textobjectstores` an update the TextObjectStorage instances
    when the files are modified

    Args:
        *textobjectstores (TextObjectStorage): the TextObjectStorage instances to be updated

    Retuns:
        (Callable) a function which stops the coroutine
    """
    return asyncio.run(asyncwatch(*textobjectstores))

async def asyncwatch(*textobjectstores: TextObjectStorage):
    obs = observers.Observer()
    for st, path in [(st, p) for st in textobjectstores for p in st.files]:
        obs.schedule(st, str(path.parent), recursive=False)
    async def _watch():
        obs.start()
        while obs.is_alive:
            await asyncio.sleep(0.5)
    asyncio.create_task(_watch())
    return lambda: obs.stop()




#
#Fooooooo
# """Context manager which updates a :obj:`TextObjectStorage`
    # each time any of the underlying files are changed"""

    # def __init__(self, *textobjectstores):
        # self.textobjectstores = textobjectstores

    # def __enter__(self):
        # self.stopfunc = watch(*self.textobjectstores)

    # def __exit__(self, type, value, traceback):
        #
#
#
# class TextObjectStorageSyncronization:
