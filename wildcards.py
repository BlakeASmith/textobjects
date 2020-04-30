"""Wildcards for template strings"""
import re
from typedef import *
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Mapping, Callable, Literal
from functools import wraps
from collections import UserList

wildcards = {}

@dataclass
class Wildcard:
    symbol: str
    action: Callable
    kind: Literal['preamble', 'postamble', 'transformation']

    def __post_init__(self):
        wildcards[self.symbol] = self

class Wildcards(UserList):
    def preambles(self):
        return [wc.action for wc in self if wc.kind == 'preamble']
    def postambles(self):
        return [wc.action for wc in self if wc.kind == 'postamble']
    def transformations(self):
        return [wc.action for wc in self if wc.kind == 'transformation']

def preamble(symbol):
    def decorator(func):
        Wildcard(symbol, func, 'preamble')
        return func
    return decorator
        
def postamble(symbol):
    def decorator(func):
        Wildcard(symbol, func, 'postamble')
        return func
    return decorator

def store_result(obj, result, placeholder, ctx):
    if placeholder and placeholder.name:
        setattr(obj, placeholder.name, result)
    return (ctx, obj)

def recursive_wrap(ctx, store_func):
    @wraps(ctx.func)
    def wrap_recurse(text):
        context, obj = ctx.func(text)
        operation = ctx.template.parse(ctx.pattern, rec=True)
        subctx, subobj = operation(context.remaining_text)
        return store_func(obj, subobj, ctx.placeholder, subctx)
    return wrap_recurse

def transformation(symbol, store_func=store_result, recurse_func=recursive_wrap):
    def decorator(func):
        @wraps(func)
        def evaluate(ctx: EvaluationContext):
            if isinstance(ctx.pattern, list):
                return recurse_func(ctx, store_func)
            else:
                @wraps(ctx.func)
                def wrap_pattern(text):
                    context, obj = ctx.func(text)
                    subcontext, result = func(context.remaining_text, ctx.pattern, context)
                    return store_func(obj, result, ctx.placeholder, subcontext)
                return wrap_pattern
        Wildcard(symbol, evaluate, 'transformation')
        return evaluate
    return decorator

def __apply_options_with_match(match, pattern, text, ctx):
    if not match:
        raise ValueError(f'{text} does not match {pattern.pattern}')
    ctx.remaining_text = text[match.end(0):]
    namedgroups = match.groupdict()

    try:
        result = [match.group(grp) if not isinstance(grp, str) else namedgroups[grp]
                  for grp in ctx.options.capture_groups]
    except:
        result = match.group(0)

    if ctx.options.strip_whitespace:
        if isinstance(result, list):
            result = [it.strip() for it in result]
        else:
            result = result.strip()
    if len(result) == 1:
        result = result[0]
    return (ctx, result) 

def __search_recurse(ctx, store_func):
    @wraps(ctx.func)
    def wrap_recurse(text):
        context, obj = ctx.func(text)
        operation = ctx.template.parse(ctx.pattern, rec=True)
        searchtext = context.remaining_text
        while searchtext:
            try: 
                subctx, subobj = operation(searchtext)
                context.remaining_text = subctx.remaining_text
                return store_func(obj, subobj, ctx.placeholder, context)
            except:
                searchtext = searchtext[1:]
        raise ValueError
    return wrap_recurse

@transformation('/', recurse_func=__search_recurse)
def search(text, pattern, ctx):
    match = pattern.search(text)
    return __apply_options_with_match(match, pattern, text, ctx)



@transformation('=')
def match(text: str, pattern: Pattern, ctx:ExecutionContext):
    match = pattern.match(text)
    return __apply_options_with_match(match, pattern, text, ctx)

def parse(wcstr: str):
    wc_regex = "|".join(wildcards).replace('?', '\?')
    wc_syms = re.findall(wc_regex, wcstr)
    wcs = [wildcards[sym] for sym in wc_syms]
    return Wildcards(wcs)


