"""Wildcards for template strings"""
import re
from typedef import *
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Mapping
from functools import wraps

class Wildcard(ABC):
    """Base class for wildcards. The purpose of this class is to simplify wrapping
    TemplateTransformations and automatically maintain a mapping of the defined wildcards.

    Args: 
        symbol (str): The symbol which will specify the wildcard in the Placeholder string

        default (boolean): Sets the subclass as the default wildcard. 
             When no wildcards are given in a Placeholder the transformation for this wildcard will be applied

    Note:
        Subclasses of wildcard are not instantiable. The __init__() method of any 
        subclass is replaced by

        .. code:: 

            def __init__(self): 
                raise NotImplementedError('Wildcard classes cannot be instantiated')

    """
    types: Mapping[str, 'Wildcard'] = {}
    """A mapping from the Wildcard names to the Wildcard subclasses"""
    types_by_symbol: Mapping[str, 'Wildcard'] = {}
    """A mapping from the Wildcard symbols to the Wildcard subclasses"""
    default_transformation = None
    """The template.TemplateTransformation used if no Wildcards are present in the Placeholder"""

    def __init_subclass__(cls, symbol, *args, default=False, **kwargs):
        super(Wildcard, cls).__init_subclass__(*args, **kwargs)
        def evaluate(ctx: EvaluationContext) -> TemplateTransformation:
            if isinstance(ctx.pattern, list):
                @wraps(ctx.func)
                def wrap_recurse(text):
                    context, obj = ctx.func(text)
                    eval_func =  ctx.template.parse(ctx.pattern, rec=True)
                    return cls.handle_wildcard(context, obj, eval_func, ctx)
                return wrap_recurse
            else:
                @wraps(ctx.func)
                def wrap_pattern(text):
                    context, obj = ctx.func(text)
                    def transform(text, pattern=ctx.pattern, context=context):
                        return cls.handle_pattern(text, pattern, context)
                    return cls.handle_wildcard(context, obj, transform, ctx)
                return wrap_pattern

        cls.symbol = symbol
        if cls.__name__ not in Wildcard.types:
            Wildcard.types[cls.__name__] = cls
            Wildcard.types_by_symbol[symbol] = cls
        else:
            raise Warning(f'there is already a {self.name} wildcard')
        if not Wildcard.default_transformation and default:
            Wildcard.default_transformation = evaluate
        elif default:
            raise Exception('there is already a default evaluator')

        def __init__(self): raise NotImplementedError('Wildcard classes cannot be instantiated')
        cls.__init__ = __init__

    def __str__(self):
        return self.symbol

    @classmethod
    def parse(cls, wildcards: str):
        wc_regex = "|".join(cls.types_by_symbol).replace('?', '\?')
        wildcards = re.findall(wc_regex, wildcards)
        if not wildcards:
            return [cls.default_transformation]
        return [cls.types_by_symbol[sym] for sym in wildcards]

    @classmethod
    @abstractmethod
    def handle_pattern(cls, text:str, 
            pattern: Pattern, ctx: ExecutionContext) -> Tuple[ExecutionContext, SimpleNamespace]:
        """This method handles the case that the subexpression for a placeholder is 
        just a python regular expression. The method should produce a TemplateTransformation
        using the pattern

        Args:
            pattern (re.RegexObject): The compiled pattern replating to the current placeholder
            ctx (template.ExecutionContext): The execution context for the transformation

        Returns:
            (~template.TemplateTransformation): a TemplateTransformation to be applied. The storage of the 
            result will be handled in `Wildcard.handle_pattern` Here's an example
            which just matches the text against the regex and returns the matched text to be stored

            .. code::
                
                @classmethod
                def handle_pattern(cls, pattern, ctx):
                    def transform(text):
                        match = pattern.match(text)
                        if not match:
                            raise ValueError(f'{text} does not match {pattern}')
                        ctx.remaining_text = ctx.remaining_text[match.end(0):]
                        return (ctx, match.group(0))
                    return transform


        """
        pass

    @classmethod
    def handle_wildcard(cls, ctx: ExecutionContext, obj: SimpleNamespace, 
            transform: TemplateTransformation, eval_ctx: EvaluationContext):
        """Handles storage and forwarding of the data produced from 
        the TemplateTransformation for this wildcard. 

        By default it stores the return of `transform` as an attribute of `obj` if the 
        ExecutionContext.Placeholder is definded and has a name

        .. code:: 

            subctx, subobj = transform(ctx.remaining_text)
            if ctx.placeholder and ctx.placeholder.name:
                setattr(obj, ctx.placeholder.name, subobj)
            return (subctx, obj)

        Args:
            ctx (~template.ExecutionContext): the execution context
            obj (SimpleNamespace): the namespace in which placeholder results can be stored 
            transform (template.TemplateTransformation): The transformation which is to be applied 

        Returns:
            (Tuple[~template.ExecutionContext, SimpleNamespace]): a tuple containing the updated execution context and
            the updated `obj`

        """
        subctx, subobj = transform(ctx.remaining_text)
        if eval_ctx.placeholder and eval_ctx.placeholder.name:
            setattr(obj, eval_ctx.placeholder.name, subobj)
        return (subctx, obj)

class MatchWildcard(Wildcard, symbol='=', default=True):

    @classmethod
    def handle_pattern(cls, text: str, pattern: Pattern, ctx:ExecutionContext):
        match = pattern.match(text)
        if not match:
            raise ValueError(f'{text} does not match {pattern.pattern}')
        ctx.remaining_text = ctx.remaining_text[match.end(0):]
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
class RepeatMatch(Wildcard, symbol='!'):
    @classmethod
    def handle_pattern(pattern: Pattern) -> TemplateTransformation:
        pass

    @classmethod
    def handle_wildcard(ctx: EvaluationContext, obj, evaluation: TemplateTransformation):
        pass

    # if not isinstance(ctx.pattern, list):
        # def repeatmatch_placeholder(text, func=ctx.func, pattern=ctx.pattern, placeholder=ctx.placeholder):
            # context, obj = func(text)
            # results, subtext, count = [], context.text, 0
            # while True:
                # match = pattern.match(subtext)
                # if not match or count == placeholder.limit:
                    # break
                # count += 1
                # subtext = subtext[match.end(0):]
                # results.append(match.group(0))
            # setattr(obj, placeholder.name, results)
            # context.text = subtext
            # return (context, obj)
    # else:
        # def repeatmatch_placeholder(text, func=func, ctx=ctx):
            # context, obj = func(text)
            # fun = create_eval_function(pattern)
            # returntext = context.text
            # results = []
            # while True:
                # try:
                    # subcontext, subobj = fun(context.text)
                    # if subtext:
                        # returntext = subcontext.text
                        # results.append(subobj)
                # except:
                    # break
            # setattr(obj, ctx.placeholder.name, results)
            # context.text = returntext
            # return (context, obj)
    # return repeatmatch_placeholder

class LooseRepeatMatch(Wildcard, symbol='!!'):
    @classmethod
    def handle_pattern(pattern: Pattern) -> TemplateTransformation:
        pass

    @classmethod
    def handle_wildcard(ctx: EvaluationContext, obj, evaluation: TemplateTransformation):
        pass
    # func, pattern, placeholder = ctx.func, ctx.pattern, ctx.placeholder
    # if not isinstance(pattern, list):
        # def findall_placeholder(text, func=func):
            # context, obj = func(text)
            # matches = pattern.finditer(context.text)
            # if not matches:
                # raise ValueError("{context.text} does not match {pattern.pattern}")
            # results = [m.group(0) for m in matches]
            # for res in results:
                # context.text = context.text.replace(res, '')
            # results = results[:min(len(results), placeholder.limit)]
            # setattr(obj, placeholder.name, results)
            # return (context, obj)
    # else:
        # def findall_placeholder(text, func=func):
            # context, obj = func(text)
            # results, returntext = [], context.text
            # eval_func = create_eval_function(pattern, search=True)
            # while True:
                # subcontext, subobj = eval_func(subtext)
                # results.append(subobj)
                # if not subcontext.text:
                    # break
                # returntext = subtext
            # setattr(obj, placeholder.name, results)
            # return (returntext, obj)
    # return findall_placeholder

class OptionalWildcard(Wildcard, symbol='?'):
    @classmethod
    def handle_pattern(pattern: Pattern) -> TemplateTransformation:
        pass

    @classmethod
    def handle_wildcard(ctx: EvaluationContext, obj, evaluation: TemplateTransformation):
        pass

class LooseMatch(Wildcard, symbol='=>'):
    @classmethod
    def handle_pattern(pattern: Pattern) -> TemplateTransformation:
        pass

    @classmethod
    def handle_wildcard(ctx: EvaluationContext, obj, evaluation: TemplateTransformation):
        pass

    # def search_pattern(text, func=ctx.func, pattern=ctx.pattern, placeholder=ctx.placeholder):
        # context, obj = func(text)
        # subtext = context.text
        # if not isinstance(pattern, list):
            # match = pattern.search(subtext)
            # if not match:
                # raise ValueError(f"could not find {pattern.pattern} in {subtext}")
            # context.text = subtext[match.end(0):]
            # if placeholder:
                # setattr(obj, placeholder.name, match.group(0))
            # return (context, obj)

        # searchmatches = pattern[0][1].finditer(subtext)
        # fun = create_eval_function(pattern[1:])
        # result = None
        # for match in searchmatches:
            # try:
                # subcontext, subobj = fun(context.text[match.end(0):])
                # return (subcontext, subobj)
            # except:
                # pass
        # raise ValueError(f"search failed")
    # return search_pattern
