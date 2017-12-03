#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Language profile: UK English
Latest version can be found at https://github.com/letuananh/chirptext

References:
    Python documentation:
        https://docs.python.org/
    PEP 0008 - Style Guide for Python Code
        https://www.python.org/dev/peps/pep-0008/
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
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

__author__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2017, chirptext"
__license__ = "MIT"
__maintainer__ = "Le Tuan Anh"
__version__ = "0.1"
__status__ = "Prototype"
__credits__ = []

########################################################################

import os
import codecs
import logging

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

logger = logging.getLogger(__name__)
MY_DIR = os.path.dirname(__file__)
MY_DATA = os.path.join(MY_DIR, 'luke_data')
DATA_FOLDER = os.path.abspath(os.path.expanduser('./data'))
SWADESH_1971_PATH = os.path.join(MY_DATA, 'swadesh/1971.txt')
SWADESH_RANKED_PATH = os.path.join(MY_DATA, 'swadesh/ranked.txt')
SWADESH_SIGN_PATH = os.path.join(MY_DATA, 'swadesh/sign.txt')


# -------------------------------------------------------------------------------
# Data structures
# -------------------------------------------------------------------------------

class Word(object):
    """ Swadesh word """
    def __init__(self, ID, word, score=0, description='', rank=0):
        self.ID = ID
        self.word = word
        self.score = score
        self.description = description
        self.rank = rank

    def __repr__(self):
        return "Word(ID={}, word={})".format(repr(self.ID), repr(self.word))


def read_swadesh_1971():
    with codecs.open(SWADESH_1971_PATH, 'r', encoding='utf-8') as infile:
        lines = infile.read().splitlines()
        table = [l.split(maxsplit=1) for l in lines if l and not l.startswith("#")]
        words = []
        for idx, row in enumerate(table):
            desc = row[1] if len(row) == 2 else ''
            word = Word(ID=idx + 1, word=row[0], description=desc)
            words.append(word)
        return words


def read_swadesh_ranked():
    with codecs.open(SWADESH_RANKED_PATH, 'r', encoding='utf-8') as infile:
        lines = infile.read().splitlines()
        table = [l.split() for l in lines if l and not l.startswith("#")]
        words = []
        for idx, row in enumerate(table):
            swid, top40, lemma, score = row
            word = Word(ID=swid, word=lemma, score=score, rank=idx + 1)
            words.append(word)
        return words


def read_swadesh_sign():
    with codecs.open(SWADESH_SIGN_PATH, 'r', encoding='utf-8') as infile:
        lines = infile.read().splitlines()
        table = [l for l in lines if l and not l.startswith("#")]
        words = []
        for idx, row in enumerate(table):
            word = Word(ID=idx + 1, word=row.strip())
            words.append(word)
        return words


# -------------------------------------------------------------------------------
# Application logic
# -------------------------------------------------------------------------------

