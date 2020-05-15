from textobjects import templates
from dataclasses import dataclass
from typing import Iterable
from collections import UserString, UserList

@dataclass
class TextObject:
    """Base class for a TextObject"""
    data: str
    """The main value of the TextObject"""
    enclosing_text: str
    """The text which the TextObject is contained in"""
    start: int 
    """the index within the `enclosing_text` at which the `data` starts"""
    end: int
    """the index within the `enclosing_text` at which the `data` ends"""
    others = []
    """items which were found while matching the TextObject, but are not named"""

    @classmethod
    def from_regex_match(cls, match, ctx):
        """create a TextObject based on a :obj:`re.MatchObject`"""
        txtobj = cls(match.group(0), ctx.fulltext, ctx.index, ctx.index + match.end(0))
        txtobj.matchobject = match
        return txtobj

    @classmethod
    def from_context(cls, ctx):
        """create a TextObject based on a :class:`Context` object"""
        txtobj = TextObject(ctx.text, ctx.fulltext, 
                ctx.index, len(ctx.fulltext))
        txtobj.__class__ = cls
        return txtobj

    def __hash__(self):
        return (hash(self.data) + 
                hash(self.enclosing_text + 
                str(self.start) + 
                str(self.end)))

class StructuredText(TextObject, UserString): 
    """A TextObject which is also a string"""

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __radd__(self, other):
        return str(self) + str(other)

class ListTextObject(TextObject, UserList): 
    """A TextObject which is also a list"""
    ...

def textobjecttypes(cls=TextObject):
    """returns a mapping from class names to classes for all 
    subclasses of TextObject"""
    classes = {}
    for subcls in cls.__subclasses__():
        classes.update(textobjecttypes(subcls))
        classes[subcls.__name__] = subcls
    return classes




    


