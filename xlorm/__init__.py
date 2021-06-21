import logging

import xlrd
import xlrd.xldate

from .util import get_xls_sheet_names
from .util import read_xls_sheet
from .util import str_clean_value
from .util import text_type


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


class XLSSheetModel(object):
    HEADER__NUM_ROWS_SKIP = 1
    conf = None
    gae_fs = False  # set to True if using excel files in the models.File filesystem

    def __init__(self, filename, sheetname, **params):
        # initialize column in instance scope
        cls = self.__class__
        for attribute in cls.__dict__.keys():
            if isinstance(cls.__dict__[attribute], Column):
                cls.__dict__[attribute].attr_name = attribute
                self.__dict__[attribute] = None
        if self.conf is None:
            self.set_header_conf()
        self.__dict__['filename'] = filename
        self.__dict__['sheetname'] = sheetname
        self.sheetname__ = sheetname
        for field in params.keys():
            self.__dict__[field] = params[field]

    @classmethod
    def _columns(cls):
        d = {}
        for attr in cls.__dict__.keys():
            col = cls.__dict__[attr]
            if isinstance(col, Column):
                d[attr] = col
        return d

    def to_dict(self, include_none=False):
        d = {}
        for attr in self.__class__._columns().keys():
            val = getattr(self, attr)
            if include_none or val is not None:
                d[attr] = val
        return d

    @classmethod
    def to_dicts(cls, models, include_none=False):
        return [m.to_dict(include_none=include_none) for m in models]

    def plain_row(self):
        cls = self.__class__
        d = {}
        for col_name in cls.conf.keys():
            col_value = self.__dict__[col_name]
            if col_value:
                d[cls.conf[col_name][0]] = col_value
            else:
                d[cls.conf[col_name][0]] = ''
        # order columns
        cols = d.keys()
        cols.sort()
        row = []
        for col_index in cols:
            row.append(d[col_index])
        return row

    @classmethod
    def headers(cls):
        dict = {}
        for col_name in cls.conf.keys():
            dict[cls.conf[col_name][0]] = col_name
        # order columns
        cols = dict.keys()
        cols.sort()
        row = []
        for col_index in cols:
            row.append(dict[col_index])
        return row

    @classmethod
    def sheetnames(cls, filename=None, file_contents=None, **params):
        sheet_names = get_xls_sheet_names(filename=filename, file_contents=file_contents)
        if len(sheet_names) > 0:
            return [sheet_names[0]]
        else:
            raise ValueError('Excel file needs at least 1 worksheet!' % (filename))

    @classmethod
    def set_header_conf(cls):
        cls.conf = {}
        for col_name in cls.__dict__:
            col = cls.__dict__[col_name]
            if isinstance(col, Column):
                if isinstance(col, TextColumn):
                    xlrd_type = xlrd.XL_CELL_TEXT
                elif isinstance(col, NumberColumn):
                    xlrd_type = xlrd.XL_CELL_NUMBER
                elif isinstance(col, DateColumn):
                    xlrd_type = xlrd.XL_CELL_DATE
                elif isinstance(col, BooleanColumn):
                    xlrd_type = xlrd.XL_CELL_BOOLEAN
                else:
                    raise AttributeError('Column type not supported (yet!): %s' + str())
                cls.conf[col_name] = (col.column_index, xlrd_type, col.column_name, col.optional,
                                      col.not_null, col.excludes, col.ignore_data_error, col.values)

    @classmethod
    def all(cls, file_contents=None, **params):
        filename = params.get('filename', 'dummy')
        sheetnames = params.get('sheetnames', cls.sheetnames(file_contents=file_contents, **params))
        return cls.all_for_sheetnames(filename, sheetnames, file_contents=file_contents)

    rows_all_cache = {}  # cached rows indexed: {filename: {sheetname: [row]}}

    @classmethod
    def all_for_sheetnames(cls, filename, sheetnames, filename_alternative=None, file_contents=None, **params):

        if cls.conf is None:
            cls.set_header_conf()
        result = []
        for sheetname in sheetnames:
            if filename.endswith('.xls') or filename.endswith('.xlsx'):
                fname = filename
            else:
                fname = filename + '.xls'
            try:
                dics = read_xls_sheet(fname, sheetname, cls.conf, cls.HEADER__NUM_ROWS_SKIP,
                                      file_contents=file_contents)
            except IOError:  # try alternative xls filename TODO: 2 b abandoned
                logging.warn('%s not found. Trying alternative filename.' % (fname))
                dics = read_xls_sheet(cls.filename_alternative() + '.xls', sheetname, cls.conf,
                                      cls.HEADER__NUM_ROWS_SKIP, file_contents=file_contents)

            rows = cls.build_from_dic_list(dics, filename, sheetname)
            # store all rows from for current sheetname in class namespace
            # cache
            if filename not in cls.rows_all_cache.keys():
                cls.rows_all_cache[filename] = {}
            cls.rows_all_cache[filename][sheetname] = rows
            result += rows
        return result

    @classmethod
    def get_primary_key(cls):
        """Returns the primary key column, if exists"""
        prim_key_field = None
        for col_name in cls.__dict__:
            if isinstance(cls.__dict__[col_name], Column):
                field = cls.__dict__[col_name]
                if field.is_primary_key:
                    if prim_key_field:
                        raise AttributeError('XLSSheetModel doesn\'t support more than one field as primary key.')
                    else:
                        prim_key_field = field
        if prim_key_field:
            return prim_key_field
        else:
            raise AttributeError('No primary key defined for "%s"' % (cls))

    @classmethod
    def get(cls, value, **params):
        """"""
        field = cls.get_primary_key()
        # TODO: to be optimized (use xlrd directly)
        rows = cls.all(**params)
        aa = None
        for row in rows:
            if row.__dict__[field.attr_name] == value:
                if aa:
                    raise ValueError(str(cls) + ': Duplicate key: ' + str(value))
                else:
                    aa = row
        return aa

    @classmethod
    def build_from_dic_list(cls, dics, filename, sheetname):
        objs = []
        for row, dic in enumerate(dics):
            obj = cls(filename, sheetname, **dic)
            # TODO: store filename, sheetname, row and col values (for saving,
            # etc.)
            obj.row = row + cls.HEADER__NUM_ROWS_SKIP + 1
            objs.append(obj)
        return objs

    def __str__(self):
        s = '['
        for attr_name in self.__class__.__dict__:
            if isinstance(self.__class__.__dict__[attr_name], Column):
                value = self.__dict__[attr_name]
                s += attr_name + ': ' + text_type(value) + '; '
        s += ']'
        return s
