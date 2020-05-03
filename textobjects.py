import template as templates
import wildcards
from collections import UserString
from typing import Pattern
from collections.abc import Iterable
from abc import ABC, abstractmethod, abstractproperty

class TextObject(ABC, UserString):
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
        cls.evaluate = templates.evaluate(template, options)

    def __init__(self, text):
        self.enclosing_text = text
        obj = self.__class__.evaluate(text)

        for k, v in vars(obj).items():
            setattr(self, k, v)
        UserString.__init__(self, obj.text)
        self.__post_init__()

    def __post_init__(self):
        pass

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
            return cls(text)
        except Exception as ex:
            raise ex
            return None

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
                return cls(looptxt)
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
                result = cls(looptxt)
                results.append(result)
                looptxt=looptxt[len(result):]
            except:
                looptxt = looptxt[1:]
        return results

def create(name, template, options=None, **kwargs):
    """create a new TextObject based on the template

    Args:
        name (str): the name of the class which will be created
        template (str): The template to base the TextObject off of
        options (typedef.Options): the options for parsing the template<Plug>_
        **kwargs: alternative to :member:`options`. a new :class:`typedef.options`
            will be created with any keyword arguments given here

    """
    options = options if options else templates.Options(**kwargs)

    class TxtObj(TextObject, template=template, options=options):
        pass
    TxtObj.__name__ = TxtObj.__qualname__ = name
    return TxtObj

def textobject(template, options=None, **kwargs):
    options = options if options else templates.Options(**kwargs)
    print(options)
    def decorator(postinit):
        cls = create(postinit.__name__, template, options)
        cls.__post_init__ = postinit
        return cls
    return decorator



