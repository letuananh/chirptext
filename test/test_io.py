#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for chio module
"""

# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import gzip
import logging
import unittest
import json
from pathlib import Path
from chirptext.anhxa import to_dict, to_obj
from chirptext import chio

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATA = os.path.join(TEST_DIR, 'data')
TEST_CSV = os.path.join(TEST_DATA, 'test.csv')


def getLogger():
    return logging.getLogger(__name__)


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


class TestIO(unittest.TestCase):

    def test_io_with_pathlib(self):
        print("Make sure that io functions works with pathlib.Path")
        # test read & write TXT
        data = [['name', 'foo'], ['age', '18']]
        json_path = Path(TEST_DATA) / 'temp.json'
        chio.write_file(json_path, json.dumps(data))
        json_data = json.loads(chio.read_file(json_path))
        self.assertEqual(json_data, data)
        # test read & write CSV
        filepath = Path(TEST_DATA) / 'temp.csv'
        chio.write_tsv(filepath, data)
        actual = chio.read_tsv(filepath)
        self.assertEqual(actual, data)

    def test_file_rw(self):
        tmpfile = os.path.join(TEST_DATA, 'test.txt')
        tmpgzfile = os.path.join(TEST_DATA, 'test.txt.gz')
        txt = 'ユニコード大丈夫だよ。'
        txtz = 'This is a zipped text file.'
        chio.write_file(content=txt, mode='wb', path=tmpfile)  # write content as bytes
        chio.write_file(tmpgzfile, content=txtz)
        # ensure that tmpgzfile is actually a gzip file
        with gzip.open(tmpgzfile, mode='rt') as infile:
            self.assertEqual(infile.read(), txtz)
        # verify written content
        self.assertTrue(chio.is_file(tmpfile))
        self.assertTrue(chio.is_file(tmpgzfile))
        self.assertEqual(chio.read_file(tmpfile), txt)
        self.assertEqual(chio.read_file(tmpgzfile), txtz)
        self.assertEqual(chio.read_file(tmpfile, mode='r'), txt)
        self.assertEqual(chio.read_file(tmpgzfile, mode='r'), txtz)
        self.assertIsInstance(chio.read_file(tmpfile, mode='rb'), bytes)
        self.assertIsInstance(chio.read_file(tmpgzfile, mode='rb'), bytes)


class TestUsingCSV(unittest.TestCase):

    def test_csv(self):
        data = [['abc', 'def\n"xyz'],
                ["'", '"', ',']]
        chio.write_csv(TEST_CSV, data)
        indata = chio.read_csv(TEST_CSV)
        self.assertEqual(data, indata)


class TestReaders(unittest.TestCase):

    def test_csv(self):
        print("Test CSV io")
        # test writing numbers => strings
        data = ((1, 2, 3), (4, 5, 6))
        chio.write_csv(TEST_CSV, data)
        indata = chio.read_csv(TEST_CSV)
        self.assertEqual(indata, [['1', '2', '3'], ['4', '5', '6']])

        # test writing strings with spaces
        data = [["Doraemon", "Nobita Nobi", "Shizuka Minamoto", "Dorami"],
                ["Takeshi Goda", "Suneo Honekawa", "Jaiko", "Hidetoshi Dekisugi"]]
        chio.write_tsv(TEST_CSV, data)
        indata = chio.read_csv(TEST_CSV)
        self.assertEqual(data, indata)

        # writing only 1 string with space?
        data = [['Takeshi Goda']]
        chio.write_tsv(TEST_CSV, data, quoting=None)
        indata = chio.read_csv(TEST_CSV)
        expected = [['Takeshi', 'Goda']]  # not quoting => CSV reader cannot guess the format
        self.assertEqual(indata, expected)
        # read file with a proper dialect
        indata = chio.read_csv(TEST_CSV, dialect='excel-tab')
        self.assertEqual(data, indata)

        # write file with forced quoting (default option)
        data = [['Takeshi Goda']]
        chio.write_tsv(TEST_CSV, data)
        indata = chio.read_csv(TEST_CSV)
        self.assertEqual(data, indata)

        # with header
        names = ["Doraemon - D001", "Nobita Nobi N001", "Shizuka Minamoto M001", "Dorami - D002",
                 "Takeshi Goda G001", "Suneo Honekawa H001", "Jaiko - G002", "Hidetoshi Dekisugi D003"]
        persons = [Person.parse(name) for name in names]
        header = ['first', 'last']
        chio.write_csv(TEST_CSV, [to_dict(p) for p in persons], fieldnames=header)
        inrows = chio.read_csv(TEST_CSV, fieldnames=True)
        getLogger().debug("Inrows: {}".format(inrows))
        expected = [{'first': 'Doraemon', 'last': '-'}, {'first': 'Nobita', 'last': 'Nobi'}, {'first': 'Shizuka', 'last': 'Minamoto'}, {'first': 'Dorami', 'last': '-'}, {'first': 'Takeshi', 'last': 'Goda'}, {'first': 'Suneo', 'last': 'Honekawa'}, {'first': 'Jaiko', 'last': '-'}, {'first': 'Hidetoshi', 'last': 'Dekisugi'}]
        self.assertEqual(inrows, expected)
        # read in as objects
        csv_rows = chio.read_csv(TEST_CSV, fieldnames=True)
        inpersons = [to_obj(Person, row) for row in csv_rows]
        expected_names = [to_obj(Person, row) for row in expected]  # without idno
        self.assertEqual(inpersons, expected_names)

        # with idno
        header = ['first', 'last', 'idno']
        chio.write_csv(TEST_CSV, [to_dict(p) for p in persons], fieldnames=header)
        inpersons = [to_obj(Person, row) for row in chio.read_csv(TEST_CSV, fieldnames=True)]
        self.assertEqual(persons, inpersons)


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
