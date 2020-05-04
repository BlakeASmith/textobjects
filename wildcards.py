"""Wildcards for template strings"""
import re
import copy
from textobjects.typedef import TemplateMatchError, EvaluationContext, \
ExecutionContext, ParsedTemplate, TemplateTransformation
import textobjects.template as template
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Mapping, Callable, Literal, Pattern, Match, Tuple
from functools import wraps
from collections import UserList
from dataclasses import dataclass

wildcards = {}

@dataclass
class Wildcard:
    """A wildcard changes the behaviour of template matching.
    register a wildcard by creating an instance of this class"""

    symbol: str
    """The symbol used in the placeholder to specify this wildcard.
    It must be unique and contain only non-alphanumeric characters 
    (`recognized by \W in a regular expression`) """
    action: Callable
    """A function which wraps the current template matching behaviour. 
    parameters will very based on the :obj:`Wildcard.kind`"""

    kind: Literal['preamble', 'postamble', 'transformation']
    """The type of wildcard. This specifies which arguments will be provided
    to :obj:`Wildcard.action` as well as the time at which the `action` 
    function will be called

        preamble: wildcards of this type will be called before processing the 
            placeholder. see :obj:`wildcards.PreambleFunction`. 
            Use decorator :func:`@preamble(symbol)` to register these

        postamble: similar to :obj:`preamble` but called after the processing
            for the placeholder has been set up. see :obj:`wildcards.PostambleFunction`. 
            Use :func:`@postamble(symbol)` to register these

        transformation: transfomrations do most of the work for matching the template string.
            transformations are applied to each pattern within the placeholder, including
            any embedded placeholders. use :func:`@transformation(symbol)` to register these.
            see :obj:`wildcards.TransformationFunction`

        """

    def __post_init__(self):
        wildcards[self.symbol] = self

PreambleFunction = Callable[[ParsedTemplate, int, EvaluationContext], TemplateTransformation]
"""The function type for a preamble"""
PostambleFunction = Callable[[ParsedTemplate, int, EvaluationContext], TemplateTransformation]
"""The function type for a postamble"""
TransformationFunction = Callable[[EvaluationContext], 
        Callable[[str], Tuple[EvaluationContext, SimpleNamespace]]]
"""The function type for a transformation"""


class Wildcards(UserList):
    """A collection of wildcards"""
    def preambles(self):
        return [wc.action for wc in self if wc.kind == 'preamble']
    def postambles(self):
        return [wc.action for wc in self if wc.kind == 'postamble']
    def transformations(self):
        return [wc.action for wc in self if wc.kind == 'transformation']

def parse(wcstr: str):
    """extract wildcard symbols from a string

    Args: 
        wcstr (str): the string containing the wildcard symbols

    Returns:
        (wildcards.Wildcards) a list of :obj:`wildcards.Wildcard`
    """
    wc_regex = "|".join(wildcards).replace('?', '\?')
    wc_syms = re.findall(wc_regex, wcstr)
    wcs = [wildcards[sym] for sym in wc_syms]
    return Wildcards(wcs)

def preamble(symbol):
    """register a PreambleFunction to be applied before building the
    template matching function for a placeholder

    Args: 
        symbol (str): the symbol which designates the preamble in the placeholder

    Returns:
        a decorator function which registers the supplied function as a preamble
    """
    def decorator(func: PreambleFunction):
        Wildcard(symbol, func, 'preamble')
        return func
    return decorator
        
def postamble(symbol):
    """register a PostambleFunction to be applied after building the
    template matching function for a placeholder

    Args: 
        symbol (str): the symbol which designates the postamble in the placeholder

    Returns:
        a decorator function which registers the supplied function as a postamble
    """
    def decorator(func: PostambleFunction):
        Wildcard(symbol, func, 'postamble')
        return func
    return decorator

def store_result(obj, result, placeholder, ctx):
    """default result storage function for matches. 
    Simply sets an attribute with the placeholder name on
    the output object"""
    if placeholder and placeholder.name:
        setattr(obj, placeholder.name, result)
    return (ctx, obj)

def recursive_wrap(ctx, store_func):
    """default handler for recursion of 
    transformations. This wraps the current
    template matching function and recursivley 
    determines the ParsedTemplate for the placeholders
    subexpression. The result is stored using the provided
    `store_func`"""
    @wraps(ctx.func)
    def wrap_recurse(text):
        context, obj = ctx.func(text)
        operation = template.evaluate(ctx.pattern, options=ctx.options, rec=True)
        try:
            subctx, subobj = operation(context.remaining_text)
            context.remaining_text = subctx.remaining_text 
            return store_func(obj, subobj, ctx.placeholder, context)
        except TemplateMatchError as tme:
            raise TemplateMatchError(str(tme), context, obj)
    return wrap_recurse

def transformation(symbol, store_func=store_result, recurse_func=recursive_wrap):
    """register a TransformationFunction to be applied to 
    each pattern within a placeholder. 

    Args:
        symbol (str): the symbol to identify the wildcard within the placeholder

        store_func: a function to store the result of the transformation onto the
            output object. It must have the same signature and return type as 
            :func:`wildcards.store_result`

        recurse_func: a function to handle the recursive element of the transformation
            (transformations of other placeholders within the placeholder). it should
            delegate to :func:`EvaluationContext.template.parse(ParsedTemplate, rec=True)`.
            It must also match the signature and return types of :func:`wildcards.recursive_wrap`

    """
    def decorator(func):
        @wraps(func)
        def evaluate(ctx: EvaluationContext):
            if isinstance(ctx.pattern, list):
                return recurse_func(ctx, store_func)
            else:
                @wraps(ctx.func)
                def wrap_pattern(text):
                    context, obj = ctx.func(text)
                    subcontext, result = func(context.remaining_text, ctx.pattern, context, obj, ctx)
                    return store_func(obj, result, ctx.placeholder, subcontext)
                return wrap_pattern
        Wildcard(symbol, evaluate, 'transformation')
        return evaluate
    return decorator

def __apply_options_with_match(match, pattern, text, ctx, obj):
    """apply options to the match and :obj:`typedef.EvaluationContext` accordingly"""
    if not match:
        raise TemplateMatchError(f'{text} does not match {pattern.pattern}', ctx, obj)
    ctx.remaining_text = text[match.end(0):]
    ctx.matched_text = ctx.text.replace(ctx.remaining_text, '')
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
    """recursion handler for the :func:`search` transformation"""
    @wraps(ctx.func)
    def wrap_recurse(text):
        context, obj = ctx.func(text)
        operation = template.evaluate(ctx.pattern, options=ctx.options, rec=True)
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
def search(text, pattern, ctx, obj, evalctx):
    """Search for the placeholder expression in the text"""
    match = pattern.search(text)
    return __apply_options_with_match(match, pattern, text, ctx, obj)

@transformation('=')
def match(text: str, pattern: Pattern, ctx:ExecutionContext, obj, evalctx):
    """match the pattern in the text"""
    match = pattern.match(text)
    return __apply_options_with_match(match, pattern, text, ctx, obj)

def __repeatmatch_recurse(ctx, store_func):
    @wraps(ctx.func)
    def wrap_recurse(text):
        context, obj = ctx.func(text)
        operation = template.evaluate(ctx.pattern, options=ctx.options, rec=True)
        results, counter = [], 0
        try: 
            while True:
                subctx, subobj = operation(context.remaining_text)
                context.remaining_text = subctx.remaining_text
                results.append(subobj)
                counter += 1
                if counter == ctx.placeholder.limit:
                    break
        except:
            store_func(obj, results, ctx.placeholder, context)
            return (context, obj)
        raise ValueError
    return wrap_recurse

@transformation('!', recurse_func=__repeatmatch_recurse)
def repeatmatch(text, pattern, ctx, obj, evalctx):
    all_results = []
    counter = 0
    without_lookahead = re.sub('\(\?\=.*?\)$', '', pattern.pattern)
    lookahead = re.search('\(\?\=(.*?)\)$', pattern.pattern)
    if lookahead:
        lookahead = lookahead.group(1)
    while True:
        match = re.match(without_lookahead, ctx.remaining_text, *ctx.options.re_flags)
        if not match:
            break
        ctx, results = __apply_options_with_match(match, pattern, ctx.remaining_text, ctx, obj)
        all_results.append(results)
        counter += 1
        if counter == evalctx.placeholder.limit:
            break
        if lookahead and re.match(lookahead, ctx.remaining_text):
            if not re.match(lookahead, ' '):
                break
    return (ctx, all_results)

def __repeatsearch_recurse(ctx, store_func):
    @wraps(ctx.func)
    def wrap_recurse(text):
        context, obj = ctx.func(text)
        operation = template.evaluate(ctx.pattern, options=ctx.options, rec=True)
        searchtext = context.remaining_text
        results = []
        counter = 0
        while searchtext:
            try: 
                subctx, subobj = operation(searchtext)
                results.append(subobj)
                counter += 1
                if counter == ctx.placeholder.limit:
                    break
                context.remaining_text = subctx.remaining_text
                searchtext = context.remaining_text
            except:
                searchtext = searchtext[1:]
        return store_func(obj, results, ctx.placeholder, context)
        raise ValueError
    return wrap_recurse

@transformation('~!', recurse_func=__repeatsearch_recurse)
def repeatsearch(text, pattern, ctx, obj, evalctx):
    matches, counter = [], 0
    without_lookahead = re.sub('\(\?\=.*?\)$', '', pattern.pattern)
    lookahead = re.search('\(\?\=(.*?)\)$', pattern.pattern)
    if lookahead:
        lookahead = lookahead.group(1)
    while True:
        match = re.search(without_lookahead, ctx.remaining_text, *ctx.options.re_flags)
        if not match:
            break
        ctx, results = __apply_options_with_match(match, pattern, ctx.remaining_text, ctx, obj)
        matches.append(results)
        counter += 1
        if counter == evalctx.placeholder.limit:
            break
        if lookahead and re.match(lookahead, ctx.remaining_text):
            if not re.match(lookahead, ' '):
                break
    return (ctx, matches)

@preamble('?')
def optional(parsedtemplate, index, ctx):
    """Optional placeholders will be captured if they are found and 
    the remainder of the template string matches. Otherwise they are ignored.
    The template string will be evaluated twice, once without the placeholder and
    once with the placeholder. If it fails to match with the placeholder then the 
    result will eventually be selected as the match without the placeholder.
    """
    @wraps(ctx.func)
    def split(text, parsedtemplate=parsedtemplate):
        context, obj = ctx.func(text)
        try:
            matches = template.evaluate(parsedtemplate[:index] 
                    + parsedtemplate[index+2:], options=ctx.options)(context.remaining_text)
            if not isinstance(matches, list):
                matches = [matches]
            for match in matches:
                if not hasattr(match, ctx.placeholder.name):
                    setattr(match, ctx.placeholder.name, None)
                    context.alternate_solutions.append(match)
        except TemplateMatchError as tme:
            pass
        return (context, obj)
    return split



