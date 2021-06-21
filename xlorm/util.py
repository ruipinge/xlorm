import datetime
import logging
import re
import sys
import unicodedata

import xlrd
import xlrd.xldate


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


RE__MULTIPLE_SPACES = re.compile(' +')


if PY3:
    integer_types = int,
    string_types = str,
    text_type = str
    integer_type = int
else:
    integer_types = (int, long)  # noqa: F821
    string_types = basestring,  # noqa: F821
    text_type = unicode  # noqa: F821
    integer_type = long  # noqa: F821


def remove_control_chars(s):
    """
    Inspiration: https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    Unicode Categories: http://www.unicode.org/reports/tr44/#GC_Values_Table
    """
    if not s:
        return s

    if PY2 and isinstance(s, str):
        s = s.decode('utf-8')
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')


def clean_str_space(s, strip=False, clean_multi_spaces=False, clean_all_spaces=False, line_joiner=' '):
    s = s.replace('\t', '  ')
    if strip:
        s = RE__MULTIPLE_SPACES.sub(' ', s.replace('\r\n', line_joiner)
                                    .replace('\n', line_joiner)
                                    .replace('\r', line_joiner)
                                    ).strip()
    else:
        s = s.rstrip()

    if clean_all_spaces:
        s = ''.join(s.split())

    return remove_control_chars(s)


def str_clean_value(value, default=None, strip=False, clean_all_spaces=False,
                    clean_multi_spaces=False, clean_line_breaks=False, line_joiner=' '):

    if isinstance(value, float):
        lvalue = integer_type(value)
        if lvalue == value:
            value = text_type(lvalue)
        else:
            value = text_type(value)

    elif isinstance(value, integer_types):
        value = text_type(value)

    elif isinstance(value, datetime.date):
        value = value.isoformat()

    elif isinstance(value, string_types):
        if clean_line_breaks:
            value = clean_str_space(value, strip=strip, clean_multi_spaces=clean_multi_spaces,
                                    clean_all_spaces=clean_all_spaces)
        else:
            value = '\n'.join([
                clean_str_space(s, strip=strip, clean_multi_spaces=clean_multi_spaces,
                                clean_all_spaces=clean_all_spaces) for s in value.split('\n')
            ])

    return value or default


def get_cell_value(sheet, rowx, colx, datemode=None):
    """ Returns a standard Python data type value for the specified xlrd cell.
    XL_CELL_DATE: datetime
    XL_CELL_NUMBER: float
    XL_CELL_EMPTY: None
    XL_CELL_TEXT: Unicode string
    XL_CELL_BOOLEAN: False or True
    """

    ctype = sheet.cell_type(rowx, colx)
    if ctype == xlrd.XL_CELL_DATE:
        try:
            dt_ = xlrd.xldate_as_tuple(sheet.cell_value(rowx, colx), datemode)
        except xlrd.xldate.XLDateNegative:
            # TODO: workaround for the google spreadsheets to excel conversion bug
            # real   export (windows)  correct (windows)   export (mac)  correct (mac)
            # 9:30   -0,604166667      0,395833333
            # 10:30  -0,5625           0,4375
            # 14:30  -0,395833333      0,604166667
            # 17:30  -0,270833333      0,729166667
            #                         =(exp. win)+1                     =(exp. mac)+3
            b = sheet.cell_value(rowx, colx)
            a = b + float(3)
            try:
                dt_ = xlrd.xldate_as_tuple(a, datemode)
            except xlrd.xldate.XLDateError:
                a = b + 1
                try:
                    dt_ = xlrd.xldate_as_tuple(a, datemode)
                except xlrd.xldate.XLDateError:
                    return b
        # time only no date component
        if dt_[0] == 0 and dt_[1] == 0 and dt_[2] == 0:
            return datetime.time(*dt_[3:])
        else:
            return datetime.datetime(*dt_)
    elif ctype == xlrd.XL_CELL_EMPTY:
        return None
    else:
        val = sheet.cell_value(rowx, colx)
        return val


def get_row_as_dict(sheet, rowx, header_conf, datemode=None):
    """ Returns a dictionary in the format {col_header: <python value>}
        corresponding for the specified xlrd row. The row represents a bank transaction.
        Returns None if row has no data."""

    dic = {}
    flag = False  # controls if all non optional columns exist
    for col_header in header_conf.keys():
        colx = header_conf[col_header][0]
        # ctype = header_conf[col_header][1]
        col_name = header_conf[col_header][2]
        optional = header_conf[col_header][3] if len(
            header_conf[col_header]) > 3 else False
        not_null = header_conf[col_header][4] if len(
            header_conf[col_header]) > 4 else False
        excludes = header_conf[col_header][5] if len(
            header_conf[col_header]) > 5 else []
        ignore_data_error = header_conf[col_header][
            6] if len(header_conf[col_header]) > 6 else False
        values = header_conf[col_header][7] if len(
            header_conf[col_header]) > 7 else None

        try:
            val = get_cell_value(sheet, rowx, colx, datemode)
        except IndexError as ie:
            if optional:
                continue
            else:
                raise ie
        except xlrd.xldate.XLDateError as de:
            # TODO: .... negative date...
            if ignore_data_error:
                val = None
            else:
                raise de
        if val in excludes:
            return None
        if not_null and val is None:
            return None
        if (values is not None and len(values) > 0) and val is not None and (val not in values):
            logging.warn('Column "%s" has not a valid value in !%s->%d->%d: %s' % (
                col_name, sheet.name, rowx + 1, colx + 1, val))
            val = None
        if not optional and val is not None:
            flag = True
        dic[col_header] = val
    if flag:
        return dic
    else:
        return None


def read_xls_sheet(fname, sheetname, header_conf, skip_header_rows=0, file_contents=None):
    """ skip_header_rows: number of header (top) rows not to be included. """

    book = xlrd.open_workbook(filename=fname, file_contents=file_contents)
    sh = book.sheet_by_name(sheetname)

    lines = []
    for rx in range(0, sh.nrows):
        # TODO: skip header rows (by header strings)
        if rx < skip_header_rows:
            continue
        try:
            btrans_dic = get_row_as_dict(sh, rx, header_conf, book.datemode)
        except xlrd.xldate.XLDateNegative:
            logging.error(fname, sheetname, rx)
            raise
        if btrans_dic:
            lines.append(btrans_dic)
    return lines


def get_xls_sheet_names(filename=None, pattern='.*', file_contents=None, **params):
    """
    params:
      file_contents: excel file contents
    """
    if file_contents:
        book = xlrd.open_workbook(file_contents=file_contents)
    else:
        book = xlrd.open_workbook(filename)
    names = book.sheet_names()
    if pattern:
        nn = []
        for name in names:
            if re.search(pattern, name):
                nn.append(name)
        names = nn
    return names
