class DynamicSerializerMixin:

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)

        super().__init__(*args, **kwargs)

        existing = set(self.fields)
        if fields is not None:
            allowed = set(fields)
            for field_name in (existing - allowed):
                self.fields.pop(field_name)

        if exclude_fields is not None:
            forbidden = existing & set(exclude_fields)
            for field_name in forbidden:
                self.fields.pop(field_name)
