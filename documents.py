import re
import typing
import collections
import operator
import asyncio
import concurrent.futures as futures
from pathlib import Path
from itertools import chain, islice
from functools import reduce
from textobjects import findall, match, matchlines, StructuredText
from textobjects.textobject import textobjecttypes

class Page(StructuredText, collections.abc.MutableSequence):
    """A block of text which contains other TextObjects"""
    def __init__(self, text='', *types, find=findall):
        super(Page, self).__init__(text, text, 0, len(text))
        self.types = types if types else textobjecttypes()
        self.__find = find
        self.__update()

    def __len__(self):
        return len(self._objects)

    def __update(self):
        self._objects = []
        for typ in self.types:
            found = self.__find(typ, self.data)
            self._objects.extend(found)
        self._objects.sort(key=lambda obj: obj.start)

    def __shift_spans(self, diff, startind):
        for it in self[startind:]:
            it.start += diff
            it.end += diff

    def update(self):
        self.__update()

    def __getitem__(self, key):
        return self._objects[key]

    def __delitem__(self, key):
        obj = self[key]
        self.data = self.data[:obj.start].rstrip() + self.data[obj.end:]
        l = len(obj)
        self.__update()
        # del self._objects[key]
        # self.__shift_spans(0-l, key)

    def __insert(self, start, end, repl):
        repl = self.__convert_to_textobject_from_str(repl)
        self.data = (self.data[:start]
                    + f'{repl.strip()}\n'
                    + self.data[end:]).lstrip()

    def __setitem__(self, key, value):
        obj = self[key]
        self.__insert(obj.start, obj.end, value)
        self._objects[key] = value
        self.__update()
        # self.__shift_spans(len(value) - len(obj), key+1)

    def __bool__(self):
        return len(self) > 0

    def __convert_to_textobject_from_str(self, txtobj):
        _txtobj = txtobj
        if not isinstance(txtobj, StructuredText):
            _txtobj = None
            for typ in self.types:
                try:
                    _txtobj = match(typ, txtobj)
                except: ...
            if not _txtobj:
                raise ValueError

        return _txtobj

    def insert(self, index, value):
        value = self.__convert_to_textobject_from_str(value)
        ind = self[index].end if index < len(self) else len(self.data)
        self.__insert(ind, ind, value)
        self.__update()
        # self._objects.insert(ind, value)
        # self.__shift_spans(len(value), index+1)

    # def sort(self, *args, **kwargs):
        # _sorted = sorted(self, *args, **kwargs)
        # for i, obj in enumerate(_sorted):
            # self[i] = obj

class ChainSequence(collections.abc.MutableSequence):
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
        for i, it in enumerate(self):
            self[i] = _sorted[i]

class Document(ChainSequence):
    """A set of TextObjects across multiple :class:`Page`"""
    def __init__(self, *pages):
        self.pages = pages
        for i, pg in enumerate(self.pages):
            pg.number = i + 1
        super(Document, self).__init__(*self.pages)

    @property
    def objects(self):
        return self.__objects

    def __contains__(self, value):
        return (value in self.pages
                or value in self.__objects)

    def pagesort(self, *args, **kwargs):
        for page in self.pages:
            page.sort()

class PageFile(Page):
    """a file containing some set of TextObjects"""
    def __init__(self, types, path, find=findall):
        self.path = Path(path).expanduser()
        super(PageFile, self).__init__('', *types, find=find)

    def __enter__(self):
        return self.open()

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.path.write_text(str(self))

    def open(self):
        self.data += self.path.read_text()
        self.update()
        return self

class DocumentFile(Document):
    def __init__(self, types, paths, find=findall):
        pages = [PageFile(types, path, find) for path in paths]
        super(DocumentFile, self).__init__(*pages)

    def __enter__(self):
        with futures.ThreadPoolExecutor() as executor:
            executor.map(lambda pg: pg.open(), self.pages)
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        with futures.ThreadPoolExecutor() as executor:
            executor.map(lambda pg: pg.close(), self.pages)
        # for pg in self.pages:
            # pg.close()

def page(filename, *types, find=findall):
    return PageFile(types, filename, find=find)

def glob(rt_dir, glob, *types, find=findall):
    files = Path(rt_dir).expanduser().glob(glob)
    files = [p for p in files if not p.is_dir()]
    return DocumentFile(types, files, find=find)
