====================================================

**textobjects** is a python module for reading arbitrary
structured data from text

Often we want to store some data programmatically, but we also need 
that data to be presented in a human readable way. There are many 
formats such as json or csv, but these may 
not always be sufficient in terms of readability. 

Other times the data format is out of our control
but we'd still like to read that text as structured data. This
is exactly what **textobjects** is for!

you can see the full docs here https://blakeasmith.github.io/textobjects/

Template Syntax
_____________________________________

**textobjects** uses a template syntax to identify a text object:

        :Placeholders: any identifier surrounded by **{ }** represents a placeholder.
                adding a placeholder creates an attribute on the textobject
                which will be set to the text which was found in that position.

        * by default a placeholder will match a single whitespace delimited word

        * you can change the matching behavior by including a **<regex>** tag.


        .. code-block:: python
                
                "{varname<regex>}" # `varname` is the name for the capture attribute
                                 # `regex` is a regular expression to match

        :Inline Regular Expressions: you can put any regular expression in the template string
                which is supported by python's `re module <https://docs.python.org/2/library/re.html>`_.
                this will affect which strings will match the template, but will not capture any data.

        .. code-block:: python
                
                "^{name<[a-z]>}$" # matches a single lowercase word on it's own line


        :Wildcards: any symbols placed between the **<regex>** tag and the placeholder identifier are interpreted 
                as **Wildcards** which change the matching behavior 


        .. code-block:: python

                "{varname<regex>/?}" # here `/` and `?` are wildcards
                "{varname/?}" # this is also valid 

Wildcards
________________________________________


        :Optional Placeholders (?): the **?** wildcard designates an *optional placeholder*. If the placeholder
                does not match it will be ignored.


        :Repeat Match (!): **!** signifies a repeating match. The placeholder will be matched 
                repeadtedly until there is some text which it does not match. The resulting matches
                will be stored as an attribute with the placeholder name on the text object.
                To match only a limited number of times you can add a number **n** after the wildcards
                in the placeholder.
                               
                .. code-block:: python

                        "{varname<regex>!n}"

                * the repeat syntax also works with regular placeholders **{varname!n}**... 

                * you can also use **~!** which will search for each occurance of the pattern and ignore any 
                  non-matching text in between

        :Embedding template strings: you can also use template string syntax within a placeholder expression.

                .. code-block:: python
                        
                        "{placeholder<{inner1} {inner2}>}"

                the resulting object will have an attribute called `placeholder` which is a an
                object with attributes `inner1` and `inner2`


.. _Examples:

Examples
====================================================================

Basic Usage
_____________________________________


Suppose we want to pull all of the 'TODO:' lines out of our source files

let's create a textobject representing a TODO:

>>> from textobjects import textobject
                
>>> ToDo = textobject('ToDo', 'TODO: {item<.*>$}')
<class ToDo>

This will take everything after the text "TODO: " as being the 
todo item. 

Then we can create one like this:

>>> todo = ToDo("TODO: make a new todo")
"make a new todo"

but not like this, since this won't match the template

Now let's pull all the TODO: lines out of a file::

        TODO: this is a todo
        TODO: this is another one
        TODO: this is a different one

>>> from pathlib import Path
>>> ToDo.findall(Path('myfile.txt').read_text())
['TODO: this is a todo', 'TODO: this is another one', 'TODO: this is a different one']

We can access the file (or a set of files) as a collection using :class:`storage.TextObjectStorage`

.. code-block:: python

        from textobjects import storage
        store = storage.TextObjectStorage([ToDo], 'myfile.txt')

:class:`storage.TextObjectStorage` implements all functions of a MutableSequence, so we can read and
modify the file as follows:

>>> for todo in store: print(todo)
TODO: this is a todo
TODO: this is another one
TODO: this is a different one

>>> print(store)
['TODO: this is a todo', 'TODO: this is another one', 'TODO: this is a different one']

>>> store += ['TODO: new todo']
['TODO: this is a todo', 'TODO: this is another one', 'TODO: this is a different one', 'TODO: new todo']

>>> del store[0]
None

>>> print(store)
['TODO: this is another one', 'TODO: this is a different one', 'TODO: new todo']

>>> store.clear()
None

>>> print(store)
[]


To monitor changes to textobjects in the file:

.. code-block:: python

        class MyObserver(storage.TextObjectObserver):
            def on_textobject_added(self, txtobj):
                print(txtobj, 'was added')
            def on_textobject_removed(self, txtobj):
                print(txtobj, 'was removed')
            def on_textobject_moved(self, txtobj):
                print(txtobj, 'was moved')

        store.subscribe(MyObserver())

Now the appropriate methods of :obj:`MyObserver()` will be called when
an item is added, removed, or moved within the storage.

Additionally we can monitor changes which occur in the storage files by using :func:`storage.sync`

.. code-block:: python

        with storage.sync(store):
           some_process()

Now, while the :func:`some_process()` is executing, the :class:`TextObjectStorage` will be
updated any time the associated files are modified. This means that the methods of 
<<<<<<< HEAD
:ob:`MyObserver()` will be called even if the textobject was added/removed/moved in the
=======
:obj:`MyObserver()` will be called even if the textobject was added/removed/moved in the
>>>>>>> e5928e57c970a612167d85d5f275ab091ef16fd5
file by some outside proccess.

Alternitivley we can use :func:`storage.watch`

.. code-block:: python

        stop = storage.watch(store)
        some_process()
        stop()












