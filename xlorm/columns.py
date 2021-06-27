from .util import str_clean_value


class Column(object):

    def __init__(self, column_index, column_name=None, default_value=None,
                 optional=False, not_null=False, excludes=[], is_primary_key=False,
                 ignore_data_error=False, values=None, **params):
        self.column_index = column_index
        self.column_name = column_name if column_name is not None else 'column' + str(column_index)
        # TODO: validate default value against column type
        self.default_value = default_value
        self.optional = optional
        # used to find a valid row/object
        self.not_null = not_null
        # used to exclude rows matching given values
        self.excludes = excludes
        self.is_primary_key = is_primary_key
        self.ignore_data_error = ignore_data_error
        self.values = values

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError(u'Instance level access only')

        cls = instance.__class__
        for att_name in cls.__dict__.keys():
            if self is cls.__dict__[att_name]:
                return instance.__dict__[att_name]
        raise AttributeError(self.var)

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError(u'Instance level access only')

        cls = instance.__class__
        for att_name in cls.__dict__.keys():
            if self is cls.__dict__[att_name]:
                instance.__dict__[att_name] = value
                return
        raise AttributeError(self.var)


class TextColumn(Column):

    def __init__(self, strip=False, multiline=True, line_joiner=' ',
                 clean_multi_spaces=True, **params):

        self.strip = strip
        self.clean_multi_spaces = clean_multi_spaces
        self.multiline = multiline
        self.line_joiner = line_joiner

        super(TextColumn, self).__init__(**params)

    def __get__(self, instance, owner):
        val = super(TextColumn, self).__get__(instance, owner)
        return str_clean_value(val, default=self.default_value,
                               strip=self.strip,
                               clean_multi_spaces=True,
                               clean_line_breaks=not self.multiline,
                               line_joiner=self.line_joiner)


class NumberColumn(Column):
    pass


class IntegerColumn(NumberColumn):
    def __get__(self, instance, owner):
        val = super(IntegerColumn, self).__get__(instance, owner)
        try:
            val = int(val)
        except ValueError:
            val = None
        except TypeError:
            val = None
        return val


class DateColumn(Column):
    pass


class BooleanColumn(Column):

    def __get__(self, instance, owner):
        return bool(super(BooleanColumn, self).__get__(instance, owner))


class TextListColumn(Column):
    # TODO:
    pass
