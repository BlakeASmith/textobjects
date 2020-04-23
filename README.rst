====================================================

**textobjects** is a python module for reading and encoding plain
text data in arbitrary formats

Often we want to store some data programmatically, but we also need 
that data to be presented in a human readable way. There are many
excellent data formats out there such as json or csv, but these may 
not always be sufficient in terms of readability. 

Other times the data format is out of our control, such as in a config or log file, 
but we'd still like to read that text as some kind of structured data. This
is exactly what **textobjects** is for!

Template Syntax
------------------------------------------------------------

**textobjects** uses string templates to create new formats:

        :Placeholders: any word surrounded by **{ }** represents a placeholder.
                adding a placeholder creates an attribute on the textobject
                which will be set to the text which was found in that position.

        * matching for placeholders is *greedy* by default. As much text 
          as possible will be matched, you can see how this works in the :ref:`Examples`


        :Inline Regular Expressions: you can put any regular expression in the template string
                which is supported by python's `re module <https://docs.python.org/2/library/re.html>`_.
                this will affect which strings will match the template, but will not capture any data.


        :Optional Placeholders: **{varname<regex>}?** is an *optional placeholder*. If the regex pattern
                matches the text at that position then the text will be captured in an attribute called
                `varname`. But if it does not match the placeholder will be ignored.


        :Repeating Matches: the syntax **{varname<regex>}!** signifies a repeating match. Any text 
                matched by the `regex` at that position will be added to a list called `varname`. This
                will be repeated until there is some text encountered which does not match the `regex`
                pattern. To match only a limited number of times you can use **<n>** where n is the
                number of matches you want, like this 
                               
                .. code-block:: python

                        {varname<regex>}!<n>

                * This is distinct from **{varname<regex>}*n** which will match exactly n times and 
                  will *fail* if there are more or fewer matches in the text

                * the repeat syntax also works with regular placeholders **{varname}!<n>**... 
                  this will capture each (whitespace delimited) token until the next pattern is found

.. _Examples:

Examples
--------------------------------------------------------------------


Suppose we want to pull all of the 'TODO:' lines out of our source files


let's create a textobject representing a TODO:

>>> from textobjects import textobject
                
>>> ToDo = textobject('ToDo', 'TODO: {item}$')
<class ToDo>

This will take everything after the text "TODO: " as being the 
todo item. 

by default additional whitespace at the beginning, end, and in-between tokens will be trimmed.
This behavior can be changed by setting the `trim_whitespace` variable on the class.

>>> ToDo.trim_whitespace = False
None
>>> ToDo = textobject('ToDo', 'TODO: {item}$', trim_whitespace=False)
<class ToDo>

Then we can create one like this:

>>> todo = ToDo("TODO: make a new todo")
ToDo(item="make a new todo")
>>> todo = ToDo(item="make a new todo")
ToDo(item="make a new todo")

but not like this, since this won't match the template

>>> todo = ToDo("TODO: can't \n have \n newlines \n")
ValueError('the given string does not match the template')

Now let's pull all the TODO: lines out of a file

>>> ToDo.findall(file='myfile.txt')

Or just the first one

>>> ToDo.search(file='myfile.txt')

Repeating Patterns
___________________________________

Much of the time there is a repeating pattern in the data. This is
easy to capture using a textobject. To illustrate this we will make a 
textobject which recognizes JSON




