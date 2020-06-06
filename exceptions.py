class TemplateMatchError(ValueError):
    def __init__(self, context, *args, **kwargs):
        super(TemplateMatchError, self).__init__(*args, **kwargs)
        self.context = context
