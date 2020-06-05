from textobjects import templates, exceptions, regex
from textobjects.textobject import StructuredText
from typing import Iterable, Mapping
from copy import deepcopy

def create(name, template, post=None, construct=None, scope={}):
    cls = templates.parse(template, name)
    if not post:
        post = lambda o: None

    init = cls.__init__
    def __init__(self, *args, scope=scope, **kwargs):
        init(self, *args, **kwargs)
        post(self)
    cls.__init__ = __init__
    __match = cls.__match__

    @classmethod
    def __match__(cls, *args, **kwargs):
        obj = __match(*args, scope=scope, **kwargs)
        post(obj)
        return obj
    cls.__match__ = __match__

    __findall = cls.__findall__

    @classmethod
    def __findall__(cls, *args, **kwargs):
        lst = __findall(*args, **kwargs)
        for obj in lst:
            post(obj)
        return lst
    cls.__findall__ = __findall__


    __search = cls.__search__

    @classmethod
    def __search__(cls, *args, **kwargs):
        obj = __search(*args, **kwargs)
        post(obj)
        return obj
    cls.__search__ = __search__

    if construct:
        new = cls.__new__
        def __new__(cls, *args, **kwargs):
            newargs = construct(*args, **kwargs)
            if isinstance(newargs, Mapping):
                return new(cls, **newargs)
            if isinstance(newargs, Iterable) and not isinstance(newargs, str):
                return new(cls, *newargs)
            return new(cls, newargs)
        cls.__new__ = __new__
    return cls

def re(name, template):
    """create a textobject class based on the template

    .. note::

        Only regular placeholders (no wildcards) are supported at this time

    """
    return regex.parse(name, template)

def match(Type: StructuredText, text: str, enclosing=None):
    return Type.__match__(text, enclosing)

def search(Type: StructuredText, text, enclosing=None):
    return Type.__search__(text, enclosing)

def findall(Type: StructuredText, text):
    return Type.__findall__(text)

def matchlines(Type: StructuredText, text: str) -> Iterable[StructuredText]:
    lines = text.split('\n')
    results = []
    for line in lines:
        try:
            m = Type.__match__(line, text)
            results.append(m)
        except:
            pass
    return results

def searchlines(Type: StructuredText, text: str) -> Iterable[StructuredText]:
    lines = text.split('\n')
    results = []
    for line in lines:
        try:
            results.append(search(Type, line, text))
        except:
            pass
    return results
