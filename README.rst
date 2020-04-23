====================================================

**textobjects** is a python module for reading and endcoding plain
text data in arbitrary formats

Often we want to store some data programatically, but we also need 
that data to be presented in a human readable way. There are many
exellent data formats out their such as json or csv, but these may 
not always be sufficient in terms of readability. 

Other times the data format is out of our control, such as in a config or log file, 
but we'd still like to read that text as some kind of structured data. This
is exactly what **textobjects** is for!

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




