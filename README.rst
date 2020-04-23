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
          as possible will be matched, you can see how this works in the `Examples`_

        * you can change the matching behavior by including a **<regex>** tag.


        .. code-block:: python
                
                {varname<regex>} # `varname` is the capture attribute
                                 # `regex` is a regular expression to match

                # this roughly translates to the regex:
                "(?P<varname>regex)"


        :Inline Regular Expressions: you can put any regular expression in the template string
                which is supported by python's `re module <https://docs.python.org/2/library/re.html>`_.
                this will affect which strings will match the template, but will not capture any data.


        .. code-block:: python
                
                ^{name<[a-z]>}$ # matches a single lowercase word on it's own line


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

                * you can also use **!!** which will match every occurance of the pattern in the 
                  text, regardless of what shows up in between, up until the end of the template


        :Referencing previous placeholders: you can reference the matches to previous placeholders
                by writing **\\g<name>** where *name* is the name of the placeholder. \\g<name> will match
                the captured text exacty and will not capture a value.

        * You can also use \\g<name> inside of the regex for a placeholder, in which case it will be captured.
        
                .. code-block:: python

                        {name<^.*\g<name>.*$>} 
                        # matches any line of text which contains whatever 
                        # was captured by placeholder 'name'
        This is the same syntax that's used by the `re module <https://docs.python.org/2/library/re.html>`_


        :Embedding other textobjects: you can embed textobjects into template strings using **{{classname}}**
                make sure that the class of the textobject is available within the enclosing scope


        :Embedding template strings: you can also use template string syntax within a placeholder regex.

                .. code-block:: python
                        
                        {placeholder<{inner1} {inner2}>}

                the resulting object will have an attribute called `placeholder` which is itself
                a textobject with attributes `inner1` and `inner2`


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

a json object begins with **{** then we can have:
        
        1. **"name":"value",** as many times as needed

        2. **"name":"value"** only once

        3. **"name":[** followed by **"value"** or **"value",** ,  and eventually **]** or **],**

then it ends with **}**

The template for this goes as follows:

.. code-block:: python
        
        """{
                {entries<"{name}":"{value},">}!!?
                {lists<"{name}":[]>}
                


        }"""












