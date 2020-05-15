import re
import os
from textobjects.placeholders import *
from textobjects.textobject import TextObject, StructuredText, ListTextObject, textobjecttypes
from textobjects.exceptions import TemplateMatchError
from collections import UserString, UserList
from anytree import RenderTree, NodeMixin
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Mapping
from functools import wraps
from copy import deepcopy
from itertools import takewhile, dropwhile

@dataclass
class Context:
    """The context object which is passed along to each nodes :func:`evaluate` function"""
    fulltext: str
    """The full text which is being matched"""
    unconsumed_text: str
    """text which has been read but not consumed, use this if you want to match against some 
    text, but some other placeholder or block later in the template string can still reference it"""
    index: int
    """the current index in the text which is being considered. This should be updated every time some part
    of the text is matched"""
    matches = []
    """The list of matches which have been discovered so far, they must either be strings, TextObject, or some other
    subclass of str. These are used in numerical backreferences like \1"""
    matchdict = {}
    """mapping of placeholder names to their matched values, used for placeholder backreferencing \<name>"""

    @property
    def text(self):
        """The remaining text which has not yet been considered, computed using :obj:`index`"""
        return self.fulltext[self.index:]

    @classmethod
    def default(cls, text:str):
        """applys defaut values for each attribute of :class:`Context` based on the given text"""
        return cls(text, text, 0)

    @classmethod
    def enclosing(cls, text, enclosing):
        last = list(re.finditer(re.escape(text), enclosing, re.M))[-1]
        ctx = cls(enclosing, text, last.start())
        return ctx

def textobject(name, rt):
    """create a StructuredText subclass from the
    given node's :func:`execute(ctx)` method

    Args:
        name (str): the name of the class
        rt (nodes.PatternNode): the root node 
    
    Returns:
        (StructuredText) a StructuredText subclass with the same 
        attributes as the result from :func:`rt.evaluate`. it will
        also have an attribute `context` which is the execution context
        returned from :func:`rt.evaluate`

    """
    if not name:
        name = 'SomeTextObject'
    class Temp(StructuredText):
        def __new__(cls, text):
            return cls.__match__(text)

        @classmethod
        def __match__(cls, text, enclosing=None):
            if not enclosing:
                enclosing = text
            ctx, result = rt.evaluate(Context.enclosing(text, enclosing))
            result.context = ctx
            return result

        @classmethod
        def __search__(cls, text, enclosing=None):
            if not enclosing:
                enclosing = text
            first = rt.firstexpression
            prospects = first.finditer(text)
            ctx = None
            for prospect in prospects:
                try:
                    ctx, result = rt.evaluate(Context.enclosing(text[prospect.start(0):], enclosing))
                    result.context = ctx
                    return result
                except TemplateMatchError:...
            raise TemplateMatchError(ctx)


        @classmethod
        def __findall__(cls, text, enclosing=None):
            if not enclosing:
                enclosing = text
            first = rt.firstexpression
            prospects = first.finditer(text)
            results = []
            for prospect in prospects:
                try:
                    ctx, result = rt.evaluate(Context.enclosing(text[prospect.start(0):], enclosing))
                    result.context = ctx
                    results.append(result)
                except TemplateMatchError: ...
            return results

    Temp.__name__ = Temp.__qualname__ = name
    return Temp

class PatternNode(NodeMixin):
    """The base node of the template parser

    Args:
        name (str): The name of the StructuredText subclass 
            produced from this node, and the name of the attribute 
            which will be added to the StructuredText subclass of 
            the parent node, if there is a parent node.

            .. note::
                
                if None is given then the result of :func:`evaluate` will
                not be stored as an attribute by the parent node.

        parent (str): The parent node
        children (str): The children of this node


    """
    def __init__(self, name=None, parent=None, children=[]):
        self.name = name
        self.parent = parent
        self.children = children

    @property
    def textobjectclass(self):
        """produce a StructuredText subclass based on this nodes :func:`evaluate` method"""
        return textobject(self.name, self)

    @property
    def firstexpression(self):
        for child in self.children:
            if hasattr(child, 'expression'):
                return child.expression
            return child.firstexpression

    def nextexpression(self, invoked_from=None):
        #TODO: refactor lookahead to use this method
        try:
            if self.children:
                for child in list(dropwhile(lambda it: it != invoked_from, self.children))[1:]:
                    if child.children:
                        return child.nextexpression(self)
                    if hasattr(child, 'expression'):
                        return child.expression
        except KeyError: pass

        if not self.parent:
            return self.expression

        return self.parent.nextexpression(self)

    def lookahead(self, pattern, invoked_from=None):
        """add a lookahead to the given pattern for the next regex expression in the template"""
        try:
            if self.children:
                for child in list(dropwhile(lambda it: it != invoked_from, self.children))[1:]:
                    if child.children:
                        return child.lookahead(pattern)
                    if hasattr(child, 'expression'):
                        return re.compile(f'{pattern.pattern}(?={child.expression.pattern})', re.M)
        except KeyError: pass

        if not self.parent:
            return pattern

        return self.parent.lookahead(pattern, self)

    def evaluate(self, ctx: Context) -> Tuple[Context, TextObject]:
        """create a StructuredText instance based on the child nodes 
        :func:`evaluate` methods::
            
            if the child node has a name, then the returned result will be stored
            as an attribute on the StructuredText instance

            if the child node does not have a name and returns a dict, then each key, 

            value pair of the dict will be added as an attribute on the StructuredText instance
        """

        txtobj = self.textobjectclass.from_context(ctx)

        results = {}
        for node in self.children:
            if node.name:
                ctx, subobj = node.evaluate(ctx)
                results[node.name] = subobj
                if subobj:
                    subobj.__class__ = node.textobjectclass
                ctx.matchdict[node.name] = subobj
            else:
                ctx, subobj = node.evaluate(ctx)
                txtobj.others.append(subobj)
                if isinstance(subobj, Mapping):
                    results.update(subobj)
            ctx.matches.append(subobj)

        txtobj.__dict__.update(results)

        txtobj.end = ctx.index
        txtobj.data = ctx.fulltext[txtobj.start:txtobj.end]

        return (ctx, txtobj)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name})'

class TextObjectNode(PatternNode):
    """A PatternNode based on the given TextObject subclass. 
    it acts the same as PatternNode but the class produced will be the 
    given class"""
    def __init__(self, textobjectclass, *args, **kwargs):
        self.__class = textobjectclass
        super(TextObjectNode, self).__init__(*args, **kwargs)
        if not self.name:
            self.name = self.__class.__name__

    @property
    def textobjectclass(self):
        return self.__class

class OptionalNode(PatternNode):
    """Each of the child nodes will be evaluated, If they return 
    a result that result will be used, If there is an Exception thrown then
    the attibute with the name `self.name` will be set to None"""
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
    """Repeat the actions of each of the child nodes
    until they are unsuccessful. The context returned from the 
    last successful call to :func:`evaluate` will be carried forward"""
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
    """repeatedly apply the :func:`evaluate` method for each child node, 
    if it succeeds then proceed to the next node, if it fails then advance the text
    by one character and try again, repeat this until either you run out of text
    or all the child nodes have succeeeded"""
    def evaluate(self, ctx):
        txtobj = self.textobjectclass.from_context(ctx)
        print('here')
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
        if not results:
            raise Exception

        return ctx, txtobj

class EitherNode(PatternNode):
    """evaluate each child node using a copy of the current context and return 
    the result from the first one which is successful. Essentially a logical OR"""
    def evaluate(self, ctx):
        results = {}
        for child in self.children:
            try:
                return child.evaluate(deepcopy(ctx))
            except: ...
        raise ValueError('None of the patterns matched')

def python_interpolation(expr, ctx):
    """set up the python interpolation enviroment and execute the given code

    Args:
        expr (str): the python code to execute
        ctx (Context): the current execution context

    Returns:
        (Context) the updated context
    """
    globs = {'context':ctx, 'types':textobjecttypes()}
    exec(expr[1:].strip(), None, globs)
    return ctx

def shell_interpolation(expr, ctx):
    """execute the given expression as a shell command, 
    not exactly sure what to do with this yet, TODO: probably will 
    store the result as a attribte on the TextObject """
    stdout = os.popen(expr).read()

class RegexNode(PatternNode):
    """A PatternNode based on a regular expression"""
    def __init__(self, name, expression, parent=None, children=[]):
        super(RegexNode, self).__init__(name, parent, children)
        self.expression = re.compile(expression, re.M)

class SubstitutionNode(RegexNode):
    """apply any substitution blocks from a template string, this includes
    interpolation, TextObject substitution, and variable substitution (TODO:)"""
    def __init__(self, name, expresson, substitutions, parent=None, children=[]):
        self._expresson = expresson
        firstexpresson = takewhile(lambda it: it != '`', expresson)
        super(SubstitutionNode, self).__init__(name, firstexpresson,  parent, children)
        self.substitutions = substitutions

    def evaluate(self, ctx):
        exprs = re.split('`', self._expresson)
        exprs = [expr for expr in exprs if expr]
        classnames = [sub.strip('`') for sub in self.substitutions]
        results = []
        for i, expr in enumerate(exprs):
            if expr in classnames and expr in textobjecttypes():
                obj = textobjecttypes()[expr](ctx.text)
                ctx = obj.context
                results.append(obj)
            elif expr.startswith('!'):
                ctx = python_interpolation(expr, ctx)
            elif expr.startswith('sh'):
                shell_interpolation(expr[2:].strip(), ctx)
            else:
                self.expresson = re.compile(expr, re.M)
                with_lookahead = self.lookahead(expr)
                match = re.match(with_lookahead, ctx.text, re.M)
                if not match:
                    raise TemplateMatchError(ctx, f'{with_lookahead} does not match ctx.text')
                ctx.index += len(match.group(0))

        if len(results) == 1:
            return ctx, results[0]

        return ctx, {'subobjects':results}

class RegexMatchNode(RegexNode):
    """match the current text to the given expression and
    create a StructuredText from the result"""
    def evaluate(self, ctx: Context):
        match = self.lookahead(self.expression).match(ctx.text)
        if not match:
            raise TemplateMatchError(ctx)
        txtobj = StructuredText.from_regex_match(match, ctx)
        txtobj.__class__ = self.textobjectclass
        ctx.index = ctx.index + len(txtobj)
        return (ctx, txtobj)

class RegexSearchNode(RegexNode):
    """search the current text for the given expression and
    create a StructuredText from the result"""
    def evaluate(self, ctx: Context):
        match = self.lookahead(self.expression).search(ctx.text)
        if not match:
            raise TemplateMatchError(ctx)
        txtobj = StructuredText.from_regex_match(match, ctx)
        txtobj.__class__ = self.textobjectclass
        text = ctx.fulltext[ctx.index:]
        ctx.index = ctx.index + len(txtobj)
        return (ctx, txtobj)
