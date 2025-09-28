import re
import asyncio
import time
from pathlib import Path
from itertools import product
from textobjects import textobjects
from collections.abc import MutableSequence
from abc import ABC, abstractmethod
from watchdog import events, observers

class TextObjectObserver(ABC):
    def on_textobject_removed(self, textobject, typ, path):
        pass

    def on_textobject_moved(self, textobject, previous_span, typ, path):
        pass

    def on_textobject_added(self, textobject, typ, path):
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

    def __init__(self, txtobjtypes, primaryfile=None, files=[], cache_ttl=300):
        self.txtobjtypes = txtobjtypes
        self.primaryfile = Path(primaryfile)
        self.files = [Path(f) for f in files]
        if self.primaryfile not in self.files:
            self.files.append(primaryfile)
        self._entries = None
        self.observers = []
        # File content cache with TTL
        self._file_cache = {}
        self._cache_ttl = cache_ttl

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
            if True not in [isinstance(value, typ) for typ in self.txtobjtypes]:
                changed = False
                for typ in self.txtobjtypes:
                    try:
                        value = typ(text=item)
                        changed = True
                    except:
                        pass
                if not changed:
                    raise ValueError(f'{item} is not in a supported format')
            obj = self[key]
            (typ, path) = self.entries()[obj]
            start, end = obj.span
            text = path.read_text()
            text = text[:start] + value + text[end:]
            path.write_text(text)
            self.update()
    
    def __delitem__(self, key):
            obj = self[key]
            typ, path = self.entries()[obj]
            start, end = obj.span
            text = path.read_text()
            text = text[:start] + text[end:].lstrip('\n')
            path.write_text(text)
            self.update()

    def __str__(self):
        return str(self.entries())

    def insert(self, index, item):
        if True not in [isinstance(item, typ) for typ in self.txtobjtypes]:
            changed = False
            for typ in self.txtobjtypes:
                try:
                    item = typ(text=item)
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
                pf.write(str(item).strip('\n') + '\n')
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
        if Path(event.src_path).name in [p.name for p in self.files]:
            # Invalidate cache for modified file
            cache_key = str(Path(event.src_path))
            if cache_key in self._file_cache:
                del self._file_cache[cache_key]
            self.update()

    def _get_file_content(self, path):
        """Get file content with caching"""
        current_time = time.time()
        cache_key = str(path)
        
        if cache_key in self._file_cache:
            content, timestamp = self._file_cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                return content
        
        # Read file and cache it
        content = path.read_text()
        self._file_cache[cache_key] = (content, current_time)
        return content

    def update(self):
        old = self._entries
        self._entries = {obj: (typ, p) for (p, typ) in product(self.files, self.txtobjtypes) 
                        for obj in typ.findall(self._get_file_content(p))}
        self.__determine_changes(old, self._entries)

    def __determine_changes(self, old, new):
        added = []
        if old is None:
            added = new.keys()
        else:
            newset, oldset = set(new), set(old)
            added = list(newset - oldset)
            removed = list(oldset - newset)

            # Create hash maps for efficient lookup instead of O(n²) product
            old_by_content = {}
            new_by_content = {}
            
            for obj in oldset:
                content_key = (obj.data, obj.start, obj.end)
                old_by_content[content_key] = obj
                
            for obj in newset:
                content_key = (obj.data, obj.start, obj.end)
                new_by_content[content_key] = obj
            
            # Find moved objects efficiently
            for obj in newset:
                if obj in oldset:
                    old_obj = old[obj]
                    if old_obj and old_obj.span != obj.span:
                        for obs in self.observers:
                            obs.on_textobject_moved(obj, old_obj.span, *new[obj])

            for txtobj in removed:
                for obs in self.observers:
                    obs.on_textobject_removed(txtobj, *old[txtobj])

        for txtobj in added:
            for obs in self.observers:
                obs.on_textobject_added(txtobj, *new[txtobj])

class TextObjectDirectoryTree(TextObjectStorage):
    """A TextObjectStorage spanning a directory structure

    Args:
        txtobjtypes (List[TextObject]): The TextObject subclasses which will be considered
        writefile (str): The path to the file which newly added items will be written to.
            it can be any file and entries will be placed at the end of the file. If the file
            does not exist a new one will be created
        root (str): Path to the root directory 
        glob (str): the glob pattern to look for within the root directory 
        recursive (bool): if true subdirectories will be considered recursivly, equivelant to 
            prepending **/ to the glob

    """
    def __init__(self, txtobjtypes, writefile, root, glob, recursive=False):
        self.txtobjtypes = txtobjtypes
        self.primaryfile = Path(writefile)
        if not self.primaryfile.exists():
            self.primaryfile.touch()
        self.root = Path(root)
        if recursive:
            files = self.root.rglob(glob)
        else:
            files = self.root.glob(glob)
        self.files = list(files)

        if self.primaryfile not in self.files:
            self.files.append(self.primaryfile)

        self._entries = None
        self.observers = []
        self.update()

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














