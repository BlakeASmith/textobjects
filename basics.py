from textobjects import textobjects

@textobjects.textobject("\[{items<'.*',?\s*(?!\])>!}\]")
def PythonList(obj):
    obj.items = [it.strip().strip(',') for it in obj.items]

