import re
import asyncio
from pathlib import Path
from itertools import product
from textobjects import textobjects
from collections.abc import MutableSequence
from abc import ABC, abstractmethod
from watchdog import events, observers



class TextObjectObserver(ABC):
    def on_textobject_removed(self, textobject):
        pass

    def on_textobject_moved(self, textobject, previous_span):
        pass

    def on_textobject_added(self, textobject):
        pass



class TextObjectStorage(MutableSequence, events.FileSystemEventHandler):
    """Persistant storage of :class:`textobjects.TextObject` subclasses
    abstracted as a mutable sequence

    Attributes:
        txtobjtypes (List[textobjects.TextObject]): The TextObject subclasses which
            will be stored 

        primaryfile (str): the path to the primary storage file. Entries will be 
            added to this file when a new item is added.

        files (List[str]): the paths to any storage files. All occurances of 
            the :obj:`txtobjtypes` in these files will show up in the sequence.
            When a textobject is updated the occurance of it in it's respective file 
            will be replaced.
    """

    def __init__(self, txtobjtypes, primaryfile, files=[]):
        self.txtobjtypes = txtobjtypes
        self.primaryfile = Path(primaryfile)
        self.files = [Path(f) for f in [primaryfile] + files]
        self._entries = None
        self.observers = []

    def entries(self, updated=False):
        if updated or not self._entries:
            self.update()
        return self._entries

    def __len__(self):
        return len(self.entries())
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.entries())[key]
        else:
            return self.entries().keys()[key]

    def __setitem__(self, key, value):
            obj = self[index]
            (typ, path) = self.entries()[obj]
            start, end = obj.span
            text = path.read_text()
            text = text[:start] + item + text[end:]
            path.write_text(text)
    
    def __delitem__(self, key):
            obj = self[key]
            typ, path = self.entries(False)[obj]
            start, end = obj.span
            text = path.read_text()
            text = text[:start] + text[end:]
            path.write_text(text)
            self.update()


    def __str__(self):
        return str(self.entries())

    def insert(self, index, item):
        if True not in [isinstance(item, typ) for typ in self.txtobjtypes]:
            changed = False
            for typ in self.txtobjtypes:
                try:
                    item = typ(item)
                    changed = True
                except:
                    pass
            if not changed:
                raise ValueError(f'{item} is not in a supported format')
        if index < len(self):
            obj = self[index]
            (typ, path) = self.entries()[obj]
            start, end = obj.span
            text = path.read_text()
            text = text[:end] + item + text[end:]
            path.write_text(text)
        elif index == len(self):
            with self.primaryfile.open('a') as pf:
                pf.write(str(item)+'\n')
        else:
            raise IndexError('index must not exceed len() {len(self)}')
        self.update()

    def __iter__(self):
        return iter(self.entries().keys())

    def __contains__(self, other):
        return other in self.entries()
    
    def __reversed__(self):
        return reversed(self.entries())

    def subscribe(self, observer: TextObjectObserver):
        self.observers.append(observer)

    def on_modified(self, event):
        if event.src_path in self.files:
            self.update()

    def update(self):
        old = self._entries
        self._entries = {obj: (typ, p) for (p, typ) in product(self.files, self.txtobjtypes) 
                        for obj in typ.findall(p.read_text())}
        self.__determine_changes(old, self._entries)

    def __determine_changes(self, old, new):
        added = []
        if old is None:
            added = new.keys()
        else:
            newset, oldset = set(new), set(old)
            added += newset - oldset
            removed = oldset - newset

            for obj1, obj2 in product(oldset, newset):
                if obj1 == obj2 and obj1.span != obj2.span:
                    for obs in self.observers:
                        obs.on_textobject_moved(obj2, obj1.span)

            for txtobj in removed:
                for obs in self.observers:
                    obs.on_textobject_removed(txtobj)

        for txtobj in added:
            for obs in self.observers:
                obs.on_textobject_added(txtobj)

class TextObjectStorageSyncronization:
    """Context manager which updates a :obj:`TextObjectStorage`
    each time any of the underlying files are changed"""

    def __init__(self, *textobjectstores):
        self.textobjectstores = textobjectstores

    def __enter__(self):
        self.stopfunc = watch(*self.textobjectstores)

    def __exit__(self, type, value, traceback):
        self.stopfunc

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














