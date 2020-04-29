from placeholders import Placeholder
from typing import Pattern
from typing import *
from types import SimpleNamespace
from dataclasses import dataclass


@dataclass
class ExecutionContext:
    """The context object passed along in each TemplateTransformation"""
    text: str
    """the inital text"""
    
    remaining_text: str = None
    """The portion of the text remaining after the previous TemplateTransformation"""

    consumed_text: str = None
    """the portion of text which has been consumed in a previous TemplateTransformation but can still
    be matched againsed """

TemplateTransformation = Callable[[str], Tuple[ExecutionContext, SimpleNamespace]]
"""Type definition for the function type which is composed to create an evaluator for a template"""

TemplatePattern = Union[Pattern, Iterable[Tuple[Optional[Placeholder], Pattern]]]
"""Either a parsed template or a re.RegexObject"""

@dataclass
class EvaluationContext:
    """The context object which is passed along while defining TemplateTransformations"""
    func: TemplateTransformation
    """The current TemplateTransformation"""
    placeholder: Placeholder
    """The current Placeholder being considered"""
    pattern: TemplatePattern
    """Either the Pattern to be evaluated, or parsed template of the see `template.parse`_"""
    
TemplateTransformationFactory = Callable[[EvaluationContext], TemplateTransformation]

ParsedTemplate = Iterable[Tuple[Optional[Placeholder], TemplatePattern]]
