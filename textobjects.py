import re
import textobjects.template as templates
import textobjects.wildcards as wildcards
import textobjects.placeholders as placeholders
from collections import UserString
from typing import Pattern
from collections.abc import Iterable
from abc import ABC, abstractmethod, abstractproperty

class BaseTextObject(ABC, UserString):

    @classmethod
    @abstractmethod
    def match(cls, text):
        """match the beginning of the text against the text object

        Args:
            text (str): the text to match against

        Returns:
            (:obj:`TextObject`) the textobject instance, or None if the text did
                not match

        """
        pass

    @classmethod
    @abstractmethod
    def search(cls, text):
        """search for the TextObject in the text and
        return the first occurance

        Args:
            text (str): the text to search 

        Returns:
            (TextObject) a TextObject instance or None if there is no match
        """
        pass

    @classmethod
    @abstractmethod
    def findall(cls, text):
        """find all occurances of the TextObject in the text

        Args: 
            text (str): the text to search

        Returns:
            (List[TextObject]) a list of the occurances found in the text, 
                if there are not found the list will be empty

        """
        pass

def setspan(txtobj, enclosing_text):
    start = enclosing_text.find(str(txtobj))
    end = start + len(txtobj)
    txtobj.span = (start, end)
    return txtobj

class TextObject(BaseTextObject):
    """a text object based on a template string

    Args:
        template (str): the template string
        options (str): the options for parsing the template string
            see :class:`typedef.Options`
    """
    def __init_subclass__(cls, template: str, options=templates.Options(), *args, **kwargs):
        super(TextObject, cls).__init_subclass__(*args, **kwargs)
        if options.all_matches: 
            raise NotImplementedError('all_matches option not supported')
        cls.options = options
        txtobjs = {cls.__name__:cls for cls in TextObject.__subclasses__()}
        subbed_txtobjs = re.finditer('<(@(\w+))>', template)
        subbed_tempate = template
        for pl in subbed_txtobjs:
            subbed_tempate = subbed_tempate.replace(
                    pl.group(1), txtobjs[pl.group(2)].template)
        cls.template = subbed_tempate
        cls.evaluate = templates.evaluate(cls.template, options)

    def __new__(cls, *args, text=None, **kwargs):
        self = object.__new__(cls)
        if not text:
            text = cls.__textrepr__(*args, **kwargs)
        self.enclosing_text = text
        obj = self.__class__.evaluate(text)

        for k, v in vars(obj).items():
            setattr(self, k, v)

        UserString.__init__(self, obj.text)
        cls.__pre_init__(self)
        return self

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def __textrepr__(cls, text):
        return text

    @classmethod
    def match(cls, text):
        """match the beginning of the text against the text object

        Args:
            text (str): the text to match against

        Returns:
            (:obj:`TextObject`) the textobject instance, or None if the text did
                not match

        """
        try:
            obj = cls(text=text)
            obj = setspan(obj, text)
            return obj
        except Exception as ex:
            raise ex

    @classmethod
    def search(cls, text):
        """search for the TextObject in the text and
        return the first occurance

        Args:
            text (str): the text to search 

        Returns:
            (TextObject) a TextObject instance or None if there is no match
        """
        looptxt = text
        while looptxt:
            try:
                obj = cls(text=looptxt)
                obj.enclosing_text = text
                obj = setspan(obj, text)
                return obj
            except:
                looptxt = looptxt[1:]

    @classmethod
    def findall(cls, text):
        """find all occurances of the TextObject in the text

        Args: 
            text (str): the text to search

        Returns:
            (List[TextObject]) a list of the occurances found in the text, 
                if there are not found the list will be empty

        """
        looptxt = text
        results = []
        while looptxt:
            try:
                result = cls(text=looptxt)
                result.enclosing_text = text
                result = setspan(result, text)
                results.append(result)
                looptxt=looptxt[len(result):]
            except:
                looptxt = looptxt[1:]
        return results

def create(name, template, options=None, totext=None, init=None, **kwargs):
    """create a new TextObject based on the template

    Args:
        name (str): the name of the class which will be created
        template (str): The template to base the TextObject off of
        options (typedef.Options): the options for parsing the template<Plug>_
        **kwargs: alternative to :obj:`options`. a new :class:`typedef.options`
            will be created with any keyword arguments given here

    """
    options = options if options else templates.Options(**kwargs)

    class TxtObj(TextObject, template=template, options=options):
        pass
    if init:
        TxtObj.__init__ = init
    if totext:
        TxtObj.__textrepr__ = totext
    else:
        def default_textrepr(text):
            return text
        TxtObj.__textrepr__ = default_textrepr

    TxtObj.__name__ = TxtObj.__qualname__ = name
    TxtObj.__pre_init__ = lambda self: None
    return TxtObj

def textobject(template, options=None, totext = None, **kwargs):
    """decorator for creating a TextObject with initialization from a 
    __post_init__ function

    Args:
        template (str): The template string to use
        options (typedef.Options): the options for parsing the template
        **kwargs: alternative to :obj:`Options`. any keyword arguments given 
            will be passed to the contstructor of :class:`typedef.Options`
    """
    options = options if options else templates.Options(**kwargs)
    def decorator(init):
        cls = create(init.__name__, template, options)
        cls.__pre_init__ = init
        if totext:
            cls.__textrepr__ = totext
        return cls
    return decorator



