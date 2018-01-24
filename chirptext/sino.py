# -*- coding: utf-8 -*-

'''
Tools for processing Chinese

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
import logging
from collections import defaultdict as dd
from .io import CSV
from .anhxa import to_obj, to_json


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


MY_DIR = os.path.dirname(os.path.realpath(__file__))
KANGXI_FILE = os.path.join(MY_DIR, 'data', 'sino', 'kangxi.csv')

# -------------------------------------------------------------------------------
# Data Structures
# -------------------------------------------------------------------------------

KANGXI_FIELDS = ["idseq", "radical", "variants", "strokes", "meaning", "pinyin", "hanviet", "hiragana", "romaji", "hangeul", "romaja", "frequency", "simplified", "examples"]


# -------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------

class Radical(object):

    ''' Chinese Radical
        Source: https://en.wikipedia.org/wiki/Kangxi_radical#Table_of_radicals
    '''
    def __init__(self, idseq='', radical='', variants='', strokes='', meaning='', pinyin='', hanviet='', hiragana='', romaji='', hangeul='', romaja='', frequency='', simplified='', examples=''):
        self.idseq = idseq
        self.radical = radical
        self.variants = variants
        self.strokes = strokes
        self.meaning = meaning
        self.pinyin = pinyin
        self.hanviet = hanviet
        self.hiragana = hiragana
        self.romaji = romaji
        self.hangeul = hangeul
        self.romaja = romaja
        self.frequency = frequency
        self.simplified = simplified
        self.examples = examples

    def to_json(self):
        return to_json(self)

    __KANGXI_MAP = None

    @staticmethod
    def kangxi():
        if not Radical.__KANGXI_MAP:
            kxs = CSV.read(KANGXI_FILE, header=True)
            Radical.__KANGXI_MAP = KangxiMap(kxs)
        return Radical.__KANGXI_MAP


class KangxiMap:

    def __init__(self, rads=None):
        self.radicals = []
        self.rad_map = {}     # kangxi.radical -> kangxi object
        self.id_rad_map = {}  # idseq ('1', '2', i.e. string) -> rad object
        self.strokes_map = dd(list)  # map strokes => radicals
        if rads:
            for rad in rads:
                self.add(to_obj(Radical, rad))

    @property
    def all(self):
        return [r.radical for r in self.radicals]

    @property
    def strokes(self):
        return {sc: [r.radical for r in rads] for sc, rads in self.strokes_map.items()}

    def __len__(self):
        return len(self.radicals)

    def __getitem__(self, key):
        if key in self.rad_map:
            return self.rad_map[key]
        elif key in self.id_rad_map:
            return self.id_rad_map[key]
        else:
            return self.radicals[key]  # by list index

    def __contains__(self, key):
        return key in self.rad_map or key in self.id_rad_map

    def add(self, rad):
        self.radicals.append(rad)
        self.rad_map[rad.radical] = rad
        self.id_rad_map[rad.idseq] = rad
        self.strokes_map[int(rad.strokes)].append(rad)
        # map variants & simplified
        if rad.variants:
            for v in rad.variants.split():
                self.rad_map[v] = rad
        if rad.simplified:
            for s in rad.simplified.split():
                self.rad_map[s] = rad
