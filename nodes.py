import re
from placeholders import *
from collections import UserString, UserList
from anytree import RenderTree, NodeMixin
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Mapping
from functools import wraps
from copy import deepcopy

@dataclass
class Context:
    fulltext: str
    unconsumed_text: str
    index: int

    @property
    def text(self):
        return self.fulltext[self.index:]

    @classmethod
    def default(cls, text:str):
        return cls(text, text, 0)

@dataclass
class TextObject:
    data: str = None
    enclosing_text: str = None
    start: int = None
    end: int = None

    @classmethod
    def from_regex_match(cls, match, ctx):
        txtobj = cls(match.group(0), ctx.fulltext, ctx.index, ctx.index + match.end(0))
        txtobj.matchobject = match
        return txtobj

    @classmethod
    def from_context(cls, ctx):
        txtobj = TextObject(ctx.text, ctx.fulltext, 
                ctx.index, len(ctx.fulltext))
        txtobj.__class__ = cls
        return txtobj
        
class StructuredText(TextObject, UserString): ...
class ListTextObject(TextObject, UserList): ...

def textobject(name, rt):
    if not name:
        name = 'SomeTextObject'
    class Temp(StructuredText):
        def __init__(self, text):
            ctx, result = rt.evaluate(Context.default(text))
            for k, v in vars(result).items():
                setattr(self, k, v)
    Temp.__name__ = Temp.__qualname__ = name.capitalize()
    return Temp

class PatternNode(NodeMixin):
    def __init__(self, name=None, parent=None, children=[]):
        self.name = name
        self.parent = parent
        self.children = children

    @property
    def textobjectclass(self):
        return textobject(self.name, self)

    def evaluate(self, ctx: Context) -> Tuple[Context, TextObject]:

        txtobj = self.textobjectclass.from_context(ctx)

        results = {}
        for node in self.children:
            if node.name:
                ctx, subobj = node.evaluate(ctx)
                results[node.name] = subobj
                if subobj:
                    subobj.__class__ = node.textobjectclass
            else:
                ctx, subobj = node.evaluate(ctx)
                if isinstance(subobj, Mapping):
                    results.update(subobj)

        txtobj.__dict__.update(results)

        return (ctx, txtobj)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name})'

class TextObjectNode(PatternNode):
    def __init__(self, textobjectclass, *args, **kwargs):
        self.__class = textobjectclass
        super(TextObjectNode, self).__init__(*args, **kwargs)
        if not self.name:
            self.name = self.__class.__name__

    @property
    def textobjectclass(self):
        return self.__class

class OptionalNode(PatternNode):
    def evaluate(self, ctx):
        txtobj = self.textobjectclass.from_context(ctx)
        results = {}

        for child in self.children:
            try:
                ctx, obj = child.evaluate(ctx)
                obj.__class__ = child.textobjectclass
                if child.name:
                    results[child.name] = obj
            except:
                if child.name:
                    results[child.name] = None
                pass

        if len(results) == 1:
            return ctx, list(results.values())[0]

        txtobj.__dict__.update(results)
        return (ctx, txtobj)

class RepeatNode(PatternNode):
    def evaluate(self, ctx):

        def repeat(child, ctx):
            items = ListTextObject([], ctx.fulltext, ctx.index, len(ctx.fulltext))
            previndex = ctx.index
            while ctx.index < len(ctx.fulltext):
                try:
                    ctx, obj = child.evaluate(ctx)
                    if isinstance(obj, Mapping):
                        items.extend(obj.values())
                    else: 
                        items.append(obj)
                    previndex = ctx.index
                except: 
                    break
            ctx.index = previndex
            if not items:
                raise ValueError
            return ctx, items

        txtobj = self.textobjectclass.from_context(ctx)
        results = ListTextObject([], ctx.fulltext, ctx.index, len(ctx.fulltext))
        for child in self.children:
            ctx, items = repeat(child, ctx)
            results.extend(items)

        return ctx, results

    @property
    def textobjectclass(self):
        return ListTextObject

class SearchNode(PatternNode):
    def evaluate(self, ctx):
        txtobj = self.textobjectclass.from_context(ctx)
        results = {}
        while ctx.index < len(ctx.fulltext):
            try:
                for child in self.children:
                    ctx, obj = child.evaluate(ctx)
                    if child.name: 
                        results[child.name] = obj
                    elif isinstance(obj, Mapping):
                        results.update(obj)

                for child in self.children:
                    if child.name not in results:
                        continue
                break
            except:
                ctx.index += 1

        if len(results) == 1:
            return ctx, list(results.values())[0]

        txtobj.__dict__.update(results)
        return ctx, txtobj

class EitherNode(PatternNode):
    def evaluate(self, ctx):
        results = {}
        for child in self.children:
            try:
                return child.evaluate(deepcopy(ctx))
            except: ...
        raise ValueError('None of the patterns matched')


class RegexNode(PatternNode):
    def __init__(self, name, expression, parent=None, children=[]):
        super(RegexNode, self).__init__(name, parent, children)
        self.expression = expression

class RegexMatchNode(RegexNode):
    def evaluate(self, ctx: Context):
        match = re.match(self.expression, ctx.text)
        txtobj = StructuredText.from_regex_match(match, ctx)
        txtobj.__class__ = self.textobjectclass
        ctx.index = ctx.index + len(txtobj)
        return (ctx, txtobj)

class RegexSearchNode(RegexNode):
    def evaluate(self, ctx: Context):
        match = re.search(self.expression, ctx.fulltext[ctx.index:])
        txtobj = StructuredText.from_regex_match(match, ctx)
        txtobj.__class__ = self.textobjectclass
        text = ctx.fulltext[ctx.index:]
        ctx.index = ctx.index + len(txtobj)
        return (ctx, txtobj)

if __name__ == '__main__':
    rt = PatternNode('FooObject')
    rep = RepeatNode('foos', rt)
    RegexSearchNode('foo', 'foo', rep)
    op = OptionalNode('optionals', parent=rep)
    RegexMatchNode('Bar', 'bar', op)
    RegexMatchNode('Cat', 'cat', op)
    ctx, obj = rt.evaluate(Context.default('barfoofoofoobarcat'))

    print(parse('foobar {outer{inner?}~!}'))
    




