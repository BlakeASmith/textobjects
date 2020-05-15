from textobjects import templates, exceptions
from textobjects.textobject import StructuredText
from typing import Iterable, Mapping
from copy import deepcopy

def create(name, template, post=None, construct=None):
    cls = templates.parse(template, name)
    if post:
        init = cls.__init__
        def __init__(self, *args, **kwargs):
            init(self, *args, **kwargs)
            post(self)
        cls.__init__ = __init__
        __match = cls.__match__

        @classmethod
        def __match__(cls, text, *args, **kwargs):
            obj = __match(text)
            post(obj)
            return obj
        cls.__match__ = __match__
    if construct:
        new = cls.__new__
        def __new__(cls, *args, **kwargs):
            if not args or kwargs:
                raise Exception
            newargs = construct(*args, **kwargs)
            if isinstance(newargs, Mapping):
                return new(cls, **newargs)
            if isinstance(newargs, Iterable) and not isinstance(newargs, str):
                return new(cls, *newargs)
            return new(cls, newargs)
        cls.__new__ = __new__
    return cls

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
            results.append(match(Type, line, text))
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
