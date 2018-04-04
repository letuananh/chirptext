#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test Dao Phay library

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import unittest
from chirptext import daophay


########################################################################

class TestDaoPhay(unittest.TestCase):

    def vn_sorted_arrays(self, inputs, expected):
        actual = daophay.sorted(inputs)
        self.assertEqual(expected, actual)

    def test_vn_sorted(self):
        print("Test vn sorting")
        self.vn_sorted_arrays([], [])
        self.vn_sorted_arrays(['anh', 'an'], ['an', 'anh'])
        self.vn_sorted_arrays(['anh', 'an', 'an,'], ['an', 'an,', 'anh'])
        self.vn_sorted_arrays(['uống', 'uốn', 'ương'], ['uốn', 'uống', 'ương'])
        self.vn_sorted_arrays(['sữa めいじ', 'sửa めいじ', 'sứ めいじ'], ['sửa めいじ', 'sữa めいじ', 'sứ めいじ'])
        # test inplace sorting
        a_list = ['mạ', 'má', 'mã', 'ma', 'mà', 'mả']
        a_list.sort(key=daophay.vnorder)
        print(a_list)
        expected = ['ma', 'mà', 'mả', 'mã', 'má', 'mạ']
        self.assertEqual(a_list, expected)
        # with other characters
        a_list = ['mà み', 'ma み', 'mà ま', 'ma ま']
        a_list.sort(key=daophay.vnorder)
        print(a_list)
        expected = ['ma ま', 'ma み', 'mà ま', 'mà み']
        self.assertEqual(a_list, expected)


########################################################################

if __name__ == "__main__":
        unittest.main()
