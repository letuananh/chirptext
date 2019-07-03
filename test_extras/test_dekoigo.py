#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test script for deko module

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import unittest
import logging

from chirptext import TextReport
from chirptext import deko
from chirptext.deko import KATAKANA, simple_kata2hira
from chirptext.deko import wakati, tokenize, tokenize_sent, analyse, parse
from chirptext.deko import MeCabSent, DekoText
from chirptext.dekoigo import igo_available
# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
txt = '雨が降る。'
txt2 = '猫が好きです。\n犬も好きです。'
txt3 = '猫が好きです。\n犬も好きです。\n鳥は'
txt4 = '猫が好きです。犬も好きです。鳥は'


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Test cases
# -------------------------------------------------------------------------------

class TestDekoIgo(unittest.TestCase):

    def test_import_igo(self):
        print("Testing igo-python availabilty")
        self.assertTrue(igo_available())


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
