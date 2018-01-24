#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test script for readers

Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

########################################################################

import os
import unittest
from chirptext.anhxa import to_json, to_obj
from chirptext.io import CSV

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATA = os.path.join(TEST_DIR, 'data')
TEST_CSV = os.path.join(TEST_DATA, 'test.csv')


# -------------------------------------------------------------------------------
# Data Structures
# -------------------------------------------------------------------------------

class Person:

    def __init__(self, first='', last='', idno=''):
        self.first = first
        self.last = last
        self.idno = idno

    @staticmethod
    def parse(full_name):
        parts = full_name.split()
        if len(parts) == 1:
            return Person(parts[0])
        elif len(parts) == 2:
            return Person(parts[0], parts[1])
        else:
            return Person(parts[0], parts[1], parts[2])

    def __repr__(self):
        return "Person(first={}, last={}, idno={})".format(repr(self.first), repr(self.last), repr(self.idno))

    def __eq__(self, other):
        return other and type(other) == Person and self.first == other.first and self.last == other.last and self.idno == other.idno


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------


class TestUsingCSV(unittest.TestCase):

    def test_csv(self):
        data = [['abc', 'def\n"xyz'],
                ["'", '"', ',']]
        CSV.write(TEST_CSV, data)
        indata = CSV.read(TEST_CSV)
        self.assertEqual(data, indata)


class TestReaders(unittest.TestCase):

    def test_csv(self):
        print("Test CSV io")
        # test writing numbers => strings
        data = ((1, 2, 3), (4, 5, 6))
        CSV.write(TEST_CSV, data)
        indata = CSV.read(TEST_CSV)
        self.assertEqual(indata, [['1', '2', '3'], ['4', '5', '6']])

        # test writing strings with spaces
        data = [["Doraemon", "Nobita Nobi", "Shizuka Minamoto", "Dorami"],
                ["Takeshi Goda", "Suneo Honekawa", "Jaiko", "Hidetoshi Dekisugi"]]
        CSV.write_tsv(TEST_CSV, data)
        indata = CSV.read(TEST_CSV)
        self.assertEqual(data, indata)

        # writing only 1 string with space?
        data = [['Takeshi Goda']]
        CSV.write_tsv(TEST_CSV, data, quoting=None)
        indata = CSV.read(TEST_CSV)
        expected = [['Takeshi', 'Goda']]  # not quoting => CSV reader cannot guess the format
        self.assertEqual(indata, expected)
        # read file with a proper dialect
        indata = CSV.read(TEST_CSV, 'excel-tab')
        self.assertEqual(data, indata)

        # write file with forced quoting (default option)
        data = [['Takeshi Goda']]
        CSV.write_tsv(TEST_CSV, data)
        indata = CSV.read(TEST_CSV)
        self.assertEqual(data, indata)

        # with header
        names = ["Doraemon - D001", "Nobita Nobi N001", "Shizuka Minamoto M001", "Dorami - D002",
                 "Takeshi Goda G001", "Suneo Honekawa H001", "Jaiko - G002", "Hidetoshi Dekisugi D003"]
        persons = [Person.parse(name) for name in names]
        header = ['first', 'last']
        CSV.write(TEST_CSV, [to_json(p) for p in persons], header=header)
        inrows = CSV.read(TEST_CSV, header=header)
        expected = [{'first': 'Doraemon', 'last': '-'}, {'first': 'Nobita', 'last': 'Nobi'}, {'first': 'Shizuka', 'last': 'Minamoto'}, {'first': 'Dorami', 'last': '-'}, {'first': 'Takeshi', 'last': 'Goda'}, {'first': 'Suneo', 'last': 'Honekawa'}, {'first': 'Jaiko', 'last': '-'}, {'first': 'Hidetoshi', 'last': 'Dekisugi'}]
        self.assertEqual(inrows, expected)
        # read in as objects
        csv_rows = CSV.read(TEST_CSV, header=header)
        inpersons = [to_obj(Person, row) for row in csv_rows]
        expected_names = [to_obj(Person, row) for row in expected]  # without idno
        self.assertEqual(inpersons, expected_names)

        # with idno
        header = ['first', 'last', 'idno']
        CSV.write(TEST_CSV, [to_json(p) for p in persons], header=header)
        inpersons = [to_obj(Person, row) for row in CSV.read(TEST_CSV, header=header)]
        self.assertEqual(persons, inpersons)


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
