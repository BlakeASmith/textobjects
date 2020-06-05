====================================================

.. docs: https://blakeasmith.github.io/textobjects/

**textobjects** is a python module for modelling arbitrary
patterns in plain text as structured data

**textobjects** provides a simple templating language to define 
structured text. It can be used as a simpler alternative to 
Regular Expressions with named groups, but also has advanced features 
such as, python & shell interpolation, substitution & composition of 
textobjects, and wildcard modifiers.

You can see the full docs here https://blakeasmith.github.io/textobjects/

Template Syntax
_____________________________________

**textobjects** uses a template syntax to identify a text object:

        :Placeholders: any identifier surrounded by **< >** represents a placeholder.
                Adding a placeholder creates an attribute on the textobject
                which will be set to the text which was found in that position.

        * by default a placeholder will match up until the next whitespace character 

        * you can change the matching behavior by including a **regex** as part of the placeholder, preceded by a ':".


        .. code-block:: python
                
                "<varname:regex>" # `varname` is the name for the capture attribute
                                 # `regex` is a regular expression to match

        :Inline Regular Expressions: you can put any regular expression in the template string
                which is supported by python's `re module <https://docs.python.org/2/library/re.html>`_.
                This will affect which strings will match the template, but will not capture any data.

        .. code-block:: python
                
                "TODO: <item:.*> $" # matches the literal characters 'TODO: ' followed by any text up until the end of the text


        :Wildcards: Wildcard (modifier) symbols can be added to the placeholder to change the matching behavior, the next 
                    section describes which wildcards are available.


        .. code-block:: python

                "<varname:regex:/?>" # here `/` and `?` are wildcards
                "<varname/?>" # this is also valid 

Wildcards
________________________________________


        :Optional Placeholders (?): the **?** Wildcard designates an *optional placeholder*. If the placeholder
                does not match it will be ignored.


        :Repeat Match (!): **!** signifies a repeating match. The placeholder will be matched 
                repeatedly until there is some text which it does not match. The resulting matches
                will be stored as an attribute with the placeholder name on the text object.
                To match only a limited number of times you can add a number **n** after the wildcards
                in the placeholder.
                               
                .. code-block:: python

                        "<varname:regex:!:n}"

                * you can also use **/!** which will search for each occurrence of the pattern and ignore any 
                  non-matching text in between

        :Embedding template strings: you can also use template string syntax within a placeholder expression.

                .. code-block:: python
                        
                        "<placeholder:<inner1> <inner2>>"

                The resulting object will have an attribute called `placeholder` which is an 
                object with attributes `inner1` and `inner2`

Python & Shell Interpolation
_________________________________________

*Python* and *Shell Commands* can be interpolated within a textobject template.
This is useful for when some logic is required while the text is being processed, or
you want to perform some transformation on the data of a placeholder which depends on 
the surrounding text.

Python Interpolation
_________________________________________

Python code can be included in the textobject template as follows:

.. code-block:: python

        "`! print('this is python code')`"

To store the result of a python expression in a variable on the textobject you can do 
the following:

.. code-block:: python

        "<placeholder:`! rv = 'store this as a variable called placeholder'`>"

Here **rv** (short for return value) is a variable provided in the scope of the python interpolation block.
The attribute produced by the placeholder will be overridden by the value of **rv**. If **rv** is **None** then 
the text matched within the placeholder will be stored as normal.

Other variables available within the scope are:

:context: this is the evaluation context which is passed along as the text is being evaluated. This can be used
          to see which part of the text is currently being considered as well as what the outer/enclosing text is.
          You can also use this to advance the text as necessary by adding to the *ind* variable. See :class:`Context`
          in the docs_.

:attrs: This is a dictionary (empty) in which you can put attributes that should be 
        stored on the resulting textobject. Use this to add multiple attributes within 
        one block.

:av_text: The remaining portion of the text that has not yet been processed.

:types: A list containing any other types of TextObject which have been defined in your program.

Additionally, a **scope** parameter (dictionary) can be supplied when creating a textobject. 
Any items within that dictionary will be available in the scope of the python block.

.. code-block:: python

        myvar = "some var"
        VarSub = textobjects.create('VarSub', '<myvar:someregex`!attrs["myvar"]=myvar`>', scope=locals())

Now every instance of :class:`VarSub` will have an attribute *myvar* equal to "some var"

>>> txtobj = textobject.match(VarSub, "someregex")
>>> txtobj.myvar
"some var"
>>> txtobj
"someregex"


Shell Interpolation
______________________________

Shell commands can be added in the template as follows::

.. code-block:: python

        "`sh some_shell_command`" 

If the shell block is put within a placeholder then the value stored
for the placeholder will be output (to stdout) of the shell command.


Composition of textobjects
________________________________

Textobjects can be composed as follows

.. code-block:: python

        def parse_date(text):
                ...

        T1 = textobjects.create('T1', '<words:\w+\s*:!>')
        T2 = textobjects.create('T2', '`T1`:date:<date:`!rv = parse_date(av_text)`>', scope={'parse_date':parse_date})

Here *T2* is a textobject which will match and store any number of words up until ':date:'
and parse out a date from the text following ':date:', putting it in an attribute called date.


>>> txtobj = textobjects.match(T2, "some words here :date: 11/12/2018")
>>> txtobj.date
"11/12/2018"
>>> txtobj.words
["some ", "words ", "here "]
>>> txtobj
"some words here :date: 11/12/2018"


Regex Text Objects
_________________________________

The textobject library uses a tree structure internally in order to evaluate the textobjects and allow 
for arbirarily complex structures. Though this provides many benifits it also involves many Python 
function calls. When processing large inputs, these function calls show themselves to be quite expensive.

Since Python's **re** module is implemented in C, it is extremley fast. Regex text objects 
implement a subset of the functionality showcased above using only regular expressions, which leads to 
a much faster runtime.

At this time, only regular placeholders are supported (no wildcards, substitutions, or interpolation)

To use regex textobjects use :func:`re`

.. code-block:: python

        MyTxtObj = textobjects.re('MyTxtObj', 'someregex<placeholder:someotherregex>')





































