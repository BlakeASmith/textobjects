import time
import collections as _collections
import textobjects
from itertools import chain, islice
from pathlib import Path

class ChainSequence(_collections.abc.MutableSequence):
    """Treat a group of MutableSequence as a single Sequence"""

    def __init__(self, *sequences):
        self.sequences = sequences

    def __convert_key(self, key):
        if key < 0:
            raise NotImplementedError('negitive indexing not supported')
        end = 0
        for seq in self.sequences:
            end += len(seq)
            
            if key < end:
                return key-end, seq
        raise KeyError(key)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return islice(self, key.start, key.stop, key.step)
        conkey, seq = self.__convert_key(key)
        return seq[conkey]

    def __setitem__(self, key, value):
        conkey, seq = self.__convert_key(key)
        seq[conkey] = value

    def __delitem__(self, key):
        conkey, seq = self.__convert_key(key)
        del seq[conkey]

    def insert(self, index, value):
        if index < len(self):
            conkey, seq = self.__convert_key(index)
            seq.insert(conkey, value)
        else:
            self.sequences[-1].append(value)

    def __len__(self):
        return sum([len(s) for s in self.sequences])

    def __iter__(self):
        return chain(*self.sequences)

    def sort(self, *args, **kwargs):
        _sorted = sorted(self, *args, **kwargs)
        for i, _ in enumerate(self):
            self[i] = _sorted[i]

class PageView(_collections.abc.Sequence):
    def __init__(self, text, *types, find=textobjects.findall):
        self.data = text
        self.types = types
        self.find = find
        self._objects = self._search_text()

    def __str__(self):
        return self.data

    def _search_text(self):
        objects = []
        for typ in self.types:

            found = self.find(typ, self.data)
            objects.extend(found)
        objects.sort(key=lambda it: it.start)
        return objects

    def __getitem__(self, key):
        return self._objects[key]

    def __len__(self):
        return len(self._objects)

class Page(PageView, _collections.abc.MutableSequence):
    """A block of text which contains other TextObjects"""
    def __setitem__(self, key, value):
        self._objects[key] = value

    def __delitem__(self, key):
        self[key] = None

    def insert(self, key, value):
        self._objects.insert(key, value)

    def pop(self, index=None):
        """Since the length of this collection should not decrease pop needs
        to ignore None values"""
        ind = index if index else -1
        while not self[ind]:
            ind -= 1
        del self[ind]

    def write(self):
        """apply the changes in this collection to the text, subsituting each of the values
        with it's associated new value"""
        objects = self._search_text()
        offset = 0
        while len(objects) > len(self): # items were removed
            self.insert(0, None) 
        for old, new in zip(objects, self):
            if not new:
                new = ''
            self.data = self.data[:old.start+offset] \
                + str(new) + self.data[old.end+offset:]
            offset += len(new) - len(old)
        j = len(objects)
        while j < len(self): # items were added
            self.text = self.text.strip() + '\n' + str(self[j])
            j += 1

class PageMap(_collections.abc.MutableMapping):
    """A map interface for a Page
    
    Args:
        page (Page): The page to use as a Map
        keyfunc (Callable): a funtion to produce the unique key from
            a TextObject on the Page
    """
    def __init__(self, page, keyfunc):
        self._map = {}
        self._indices = {}
        self.page = page
        for i, obj in page:
            key = keyfunc(obj)
            self._map[key] = obj
            self._indices[key] = i

    def __len__(self):
        return len(self._map)

    def __iter__(self):
        return iter(self._map)

    def __getitem__(self, key):
        return self._map[key]

    def __setitem__(self, key, value):
        index = self._indices[key]
        self.page[index] = value
        self._map[key] = value

    def __delitem__(self, key):
        del self.page[self._indices[key]]
        del self._map[key]

class File:
    """Context manager to create a Page from a file"""
    def __init__(self, path, *types, find=textobjects.findall):
        self.path = Path(path).expanduser().absolute()
        self.file = None
        self.find = find
        self.types = types
    
    def __enter__(self):
        self.page = Page(self.path.read_text(), *self.types, find=self.find)
        self.file = self.path.open('w')
        return self.page

    def __exit__(self, type, value, traceback):
        self.page.write()
        self.file.write(self.page.data)
        print(self.page.data)
        self.file.close()

class Document(ChainSequence):
    def __init__(self, *pages):
        self.pages = list(pages)
        super(Document, self).__init__(*pages)

    def __contains__(self, value):
        """support checking for pages and individual objects"""
        return (super(Document, self).__contains__(value)
                or value in self.pages)

    def write(self):
        for page in self.pages:
            page.write()

class Archive:
    """A context manager to create a Document from a group of files"""
    def __init__(self, paths, *types, find=textobjects.findall):
        self.paths = paths
        self.types = types
        self.find = find

    def __enter__(self):
        contents = [p.read_text() for p in self.paths]
        pages = [Page(content, *self.types, find=self.find) 
                 for content in contents]
        self.document = Document(*pages)
        return self.document

    def __exit__(self, type, value, traceback):
        self.document.write()
        for page, p in zip(self.document.pages, self.paths):
            f = p.open('w') 
            f.write(page.data)
            f.close()

def open(filename, *types, find=textobjects.findall):
    return File(Path(filename), *types, find=find) 

def glob(rt_dir, glob, *types, find=textobjects.findall):
    files = Path(rt_dir).expanduser().glob(glob)
    files = [p for p in files if not p.is_dir()]
    return Archive(files, *types,  find=find)

