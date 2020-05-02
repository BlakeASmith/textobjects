import re
from placeholders import Placeholder
from typing import Pattern, Iterable, Union, Callable, Tuple, Optional, Any
from types import SimpleNamespace
from dataclasses import dataclass, field

class TemplateMatchError(ValueError):
    """A ValueError which contains the context of the TemplateEvaluator"""
    def __init__(self, message, context, obj, **kwargs):
        super(ValueError, self).__init__(message)
        self.context = context
        self.obj = obj
        for k, v in kwargs.items():
            setattr(self, k, v)

@dataclass
class Options:
    """options used in the evaluation of templates

    .. note::

        all attributes must have default values
    """
    strip_whitespace: bool = True
    """strip opening and trailing whitespace from each placeholder match"""
    strict_whitespace: bool = False
    """strictly match whitespace for placeholders"""
    capture_groups: Iterable[Union[int, str]] = (0,)
    """identifies the regex capture groups which will be used as the 
    value for a placeholder. Default is the entire match"""
    re_flags: Iterable[int] = (re.MULTILINE,)
    """flags given to `re.compile`"""
    all_matches: bool = False
    """return all possible matches to the placeholder"""

@dataclass
class ExecutionContext:
    """The context object passed along in each TemplateTransformation"""
    text: str
    """the inital text"""
    
    remaining_text: str = None
    """The portion of the text remaining after the previous TemplateTransformation"""

    consumed_text: str = None
    """the portion of text which has been consumed in a previous 
    TemplateTransformation but can still be matched againsed """

    options: Options = Options()
    """the options set for the :class:`template.TemplateEvaluator`"""

    alternate_solutions: Iterable = field(default_factory=lambda: [])
    """any found solutions can be stored here. If there is an 
    exception raised during the execution one of these solutions
    will be returned"""

TemplateTransformation = Callable[[str], Tuple[ExecutionContext, SimpleNamespace]]
"""Type definition for the function type which is composed to create an evaluator for a template"""

TemplatePattern = Union[Pattern, Iterable[Tuple[Optional[Placeholder], Pattern]]]
"""Either a parsed template or a re.RegexObject"""


@dataclass(frozen=True)
class EvaluationContext:
    """The context object which is passed along while defining TemplateTransformations"""
    func: TemplateTransformation
    """The current TemplateTransformation"""
    placeholder: Placeholder
    """The current Placeholder being considered"""
    pattern: TemplatePattern
    """Either the Pattern to be evaluated, or parsed template of the see `template.parse`_"""
    template: Any
    """The :obj:`TemplateEvaluator` which is calling the function"""

    
ParsedTemplate = Iterable[Tuple[Optional[Placeholder], TemplatePattern]]
""""""
