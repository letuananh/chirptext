# -*- coding: utf-8 -*-

"""
Tools for processing Chinese
"""

# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import logging
from collections import defaultdict as dd

from . import chio
from .anhxa import to_obj, to_dict


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

    """ Chinese Radical
        Source: https://en.wikipedia.org/wiki/Kangxi_radical#Table_of_radicals
    """
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

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "{}-{}[sc:{}]".format(self.radical, self.meaning, self.strokes)

    def to_dict(self):
        return to_dict(self)

    __KANGXI_MAP = None

    @staticmethod
    def kangxi():
        if not Radical.__KANGXI_MAP:
            kxs = chio.read_csv(KANGXI_FILE, fieldnames=True)
            Radical.__KANGXI_MAP = KangxiMap(kxs)
        else:
            getLogger().debug("Kangxi has been loaded once. Created KangxiMap will be re-used")
        return Radical.__KANGXI_MAP


class KangxiMap:

    def __init__(self, rads=None):
        self.radicals = []
        self.rad_map = {}     # kangxi.radical -> kangxi object
        self.id_rad_map = {}  # idseq ('1', '2', i.e. string) -> rad object
        self.strokes_map = dd(list)  # map strokes => radicals
        if rads:
            for rad in rads:
                rad_obj = to_obj(Radical, rad)
                rad_obj.frequency = int(rad_obj.frequency)
                rad_obj.idseq = int(rad_obj.idseq)
                rad_obj.strokes = int(rad_obj.strokes)
                self.add(rad_obj)

    @property
    def all(self):
        return [r.radical for r in self.radicals]

    @property
    def strokes(self):
        return {sc: [r.radical for r in rads] for sc, rads in self.strokes_map.items()}

    def __len__(self):
        return len(self.radicals)

    def __getitem__(self, key):
        if key in self.rad_map:  # literal matching
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
        self.id_rad_map[str(rad.idseq)] = rad
        self.strokes_map[int(rad.strokes)].append(rad)
        # map variants & simplified
        if rad.variants:
            for v in rad.variants.split():
                self.rad_map[v] = rad
        if rad.simplified:
            for s in rad.simplified.split():
                self.rad_map[s] = rad
