"""Parse template strings to create evaluator functions"""
import re
import textobjects.wildcards as wildcards
from textobjects.wildcards import Wildcard
from textobjects.placeholders import *
from textobjects.typedef import EvaluationContext, ExecutionContext, TemplateMatchError, Options
from typing import Pattern
from types import SimpleNamespace
from functools import wraps, lru_cache
from dataclasses import dataclass, replace

# Global regex pattern cache to avoid repeated compilation
_regex_cache = {}

def parse_placeholder(placeholder:str, parent=None, options=Options()):
    """extract name, expression, and wildcards from the text of a placeholder
    
    Args:
        placeholder (str): the string representing the placeholder

    Returns:
        (placeholders.Placeholder): A Placeholder from the string
    """
    match = PLACEHOLDER_PATTERN.match(placeholder).groupdict()

    default_pattern = DEFAULT_PLACEHOLDER_SUBEXPR
    if not options.strict_whitespace:
        default_pattern = f'\s*{default_pattern}\s*'

    return Placeholder(
            name = match['name'], 
            subexpr = match['subexpr'] if match['subexpr'] else default_pattern,
            wildcards = wildcards.parse(match['wildcards']),
            limit = int(match['limit']) if match['limit'] else None,
            parent=parent)

def __addpattern(pattern, lst, *flags, placeholder=None):
    if pattern:
        # Use cached regex compilation
        cache_key = (pattern, flags)
        if cache_key not in _regex_cache:
            _regex_cache[cache_key] = re.compile(pattern, *flags)
        lst.append((placeholder, _regex_cache[cache_key]))

def parse(template, parent=None, options=Options()):
    """produce a list of Patterns associated with the
    appropriate placeholder information
    
    Args:
        template (str): the template string to parse

    Returns:

    (ParsedTemplate):
        each Placeholder in the template assocated to it's pattern"""
    flags = options.re_flags
    results = []
    
    # Use regex-based parsing instead of character-by-character
    # Find all placeholders using regex
    placeholder_pattern = re.compile(r'<[^>]*>')
    last_end = 0
    
    for match in placeholder_pattern.finditer(template):
        # Add text before placeholder
        if match.start() > last_end:
            text_before = template[last_end:match.start()]
            if text_before:
                __addpattern(text_before, results, *flags)
        
        # Process placeholder
        placeholder = match.group(0)
        parsed = parse_placeholder(placeholder, options)
        if PLACEHOLDER_START in parsed.subexpr:
            results.append((parsed, parse(parsed.subexpr, parsed)))
        else:
            __addpattern(parsed.subexpr, results, *flags, placeholder=parsed)
        
        last_end = match.end()
    
    # Add remaining text
    if last_end < len(template):
        remaining_text = template[last_end:]
        if remaining_text:
            __addpattern(remaining_text, results, *flags)
    
    return results


def __adjust_by_future(parsedtemplate, options):
    if not options.strict_whitespace:
        for i, (placeholder, pattern) in enumerate(parsedtemplate):
            if isinstance(pattern, Pattern):
                loosews = re.sub('\s+', re.escape('\s+'), pattern.pattern)
                loosews = loosews.replace('\\s\+', '\s+')
                # Use cached compilation
                cache_key = (loosews, options.re_flags)
                if cache_key not in _regex_cache:
                    _regex_cache[cache_key] = re.compile(loosews, *options.re_flags)
                pattern = _regex_cache[cache_key]
                parsedtemplate[i] = (placeholder, pattern)

    for i, (placeholder, pattern) in enumerate(parsedtemplate[:-1]):
        if isinstance(pattern, list):
            parsedtemplate[i] = (placeholder, __adjust_by_future(pattern, options))
        else:
            if placeholder:
                patt = parsedtemplate[i+1][1].pattern
                if not re.search('\(\?=.*\)$', pattern.pattern):
                    lookahead = f'(?={patt})'
                    new_pattern = pattern.pattern + lookahead
                    # Use cached compilation
                    cache_key = (new_pattern, options.re_flags)
                    if cache_key not in _regex_cache:
                        _regex_cache[cache_key] = re.compile(new_pattern, *options.re_flags)
                    newpatt = _regex_cache[cache_key]
                    parsedtemplate[i] = (placeholder, newpatt)

    return parsedtemplate

def evaluate(template: str, options=Options(), rec=False):
    """evaluate the Template

    Args:
        template (str): the template string to evaluate

    Returns:
        (Callable[[str], SimpleNamespace]):
        a function to produce an object containing 
        attributes for any placeholders in the template
    """
    def func(text):
        ctx = ExecutionContext(text=text, remaining_text=text, 
                consumed_text='', options=options)
        return (ctx, SimpleNamespace())


    parsedtemplate = parse(template, options) if not isinstance(template, list) else template
    parsedtemplate = __adjust_by_future(parsedtemplate, options) 

    # apply preambles
    for i, (placeholder, pattern) in enumerate(parsedtemplate):
        context = EvaluationContext(func, placeholder, pattern, options)
        if placeholder and placeholder.wildcards:
            for pre in placeholder.wildcards.preambles():
                func = pre(parsedtemplate, i, replace(context, func=func))

    for i, (placeholder, pattern) in enumerate(parsedtemplate):
        context = EvaluationContext(func, placeholder, pattern, options)
        if placeholder and placeholder.wildcards:
            if placeholder.wildcards.transformations():
                for transform in placeholder.wildcards.transformations():
                    func = transform(replace(context, func=func))
            else:
                func = wildcards.match(replace(context, func=func))

            for post in placeholder.wildcards.postambles():
                func = post(parsedtemplate, i, replace(context, func=func))
        else: 
            func = wildcards.match(replace(context, func=func))


    if rec:
        return func

    @wraps(func)
    def wrapper(text):
        results = None
        ctx = None
        try:
            ctx, result = func(text)
            results = [result] + ctx.alternate_solutions
        except TemplateMatchError as tme:
            if tme.context.alternate_solutions:
                results = tme.context.alternate_solutions
                ctx = tme.context
            else: raise tme
        for result in results:
            result.text = ctx.matched_text
        if ctx.options.all_matches:
            return results
        else:
            return results[0]
    return wrapper
