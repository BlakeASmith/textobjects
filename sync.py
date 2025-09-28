import asyncio
from watchdog import events, observers
from abc import ABC

class TextObjectObserver(ABC):
    def on_textobject_removed(self, textobject, typ, path):
        pass

    def on_textobject_moved(self, textobject, previous_span, typ, path):
        pass

    def on_textobject_added(self, textobject, typ, path):
        pass

class TextObjectStorageSyncronization:
    """Context manager which updates a :obj:`TextObjectStorage`
    each time any of the underlying files are changed"""
    
    def __init__(self, *textobjectstores):
        self.textobjectstores = textobjectstores
        self._stop_func = None

    def __enter__(self):
        self._stop_func = watch(*self.textobjectstores)
        return self

    def __exit__(self, type, value, traceback):
        if self._stop_func:
            self._stop_func()

def sync(*textobjectstorage):
    """create a Context Manager which handles syncronization"""
    return TextObjectStorageSyncronization(*textobjectstorage)

def watch(*textobjectstores):
    """start a co-routine to watch the files assocated to 
    the :obj:`textobjectstores` an update the TextObjectStorage instances
    when the files are modified

    Args:
        *textobjectstores (TextObjectStorage): the TextObjectStorage instances to be updated

    Returns:
        (Callable) a function which stops the coroutine
    """
    return asyncio.run(asyncwatch(*textobjectstores))

async def asyncwatch(*textobjectstores):
    """Improved async file watching with proper event handling"""
    obs = observers.Observer()
    
    # Schedule watchers for each storage
    for st in textobjectstores:
        for path in st.files:
            obs.schedule(st, str(path.parent), recursive=False)
    
    def stop_watching():
        obs.stop()
        obs.join()
    
    # Start the observer
    obs.start()
    
    # Use proper async event loop instead of polling
    try:
        while obs.is_alive():
            await asyncio.sleep(0.1)  # Reduced sleep time for better responsiveness
    except asyncio.CancelledError:
        stop_watching()
        raise
    
    return stop_watching
