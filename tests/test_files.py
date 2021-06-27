#!/usr/bin/python
# -*- coding: utf-8 -*-
from xlorm.base import XLSSheetModel
from xlorm.columns import BooleanColumn, DateColumn, IntegerColumn, NumberColumn, TextColumn

from .helpers import from_sample


class Person(XLSSheetModel):
    active = BooleanColumn(column_index=0, column_name='Active')
    name = TextColumn(column_index=1, strip=True, multiline=False, column_name='Name')
    birthday = DateColumn(column_index=2, column_name='Birthday')
    age = IntegerColumn(column_index=3, column_name='Age')
    bio = TextColumn(column_index=4, column_name='Bio')
    weight = NumberColumn(column_index=5, column_name='Weight')
    rating = NumberColumn(column_index=6, column_name='Rating')
    wakeup_at = DateColumn(column_index=7, column_name='Wake-up time')
    event = DateColumn(column_index=8, column_name='Event')


class TestOpen(object):

    def test_column_types_and_values(self):
        q = Person.all(filename=from_sample('people.xlsx'), sheetname=['Sheet1'])
        assert len(q) == 7

        assert q[0].name == 'Pedro Duarte'
        assert q[0].age == 41  # Excel formula column

        assert q[1].name == 'Daniel Duarte'
        assert q[2].name == 'Francisco Martins'
        assert q[3].name == 'Fernanda Ribeiro'
        assert q[4].name == 'Marta Fernandes'
        assert q[5].name == 'Empty'
        assert q[6].name is None
