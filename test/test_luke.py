#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test script for luke

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import unittest
from chirptext.luke import read_swadesh_1971, read_swadesh_ranked, read_swadesh_sign

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATA = os.path.join(TEST_DIR, 'data')


# -------------------------------------------------------------------------------
# Test cases
# -------------------------------------------------------------------------------

class TestLuke(unittest.TestCase):

    def test_swadesh(self):
        s71 = read_swadesh_1971()
        sr = read_swadesh_ranked()
        ss = read_swadesh_sign()
        self.assertEqual(len(s71), 100)
        self.assertEqual(len(sr), 100)
        self.assertEqual(len(ss), 100)
        self.assertEqual(repr(s71[0]), "Word(ID=1, word='I')")
        # are they the same words?
        s71_words = {w.word for w in s71}
        sr_words = {w.word for w in sr}
        self.assertEqual(s71_words, sr_words)
        ss_words = {w.word for w in ss}
        self.assertEqual(len(ss_words), 100)
        # validate words
        same = ss_words.intersection(s71_words)
        diff = ss_words.difference(s71_words)
        self.assertEqual(same, {'die', 'red', 'stone', 'lie', 'leaf', 'grease', 'not', 'tree', 'mountain', 'black', 'kill', 'night', 'egg', 'louse', 'who', 'blood', 'green', 'what', 'rain', 'dry', 'good', 'sit', 'white', 'new', 'man', 'all', 'full', 'fire', 'bird', 'tail', 'woman', 'moon', 'yellow', 'water', 'name', 'feather', 'long', 'sun', 'star', 'stand', 'fish', 'dog', 'person', 'earth'})
        self.assertEqual(diff, {'when', 'wide', 'smooth', 'snow', 'laugh', 'with', 'warm', 'child', 'brother', 'cat', 'sing', 'how', 'correct', 'worm', 'dust', 'sharp', 'pig', 'play', 'meat', 'grass', 'ice', 'dull', 'short', 'animal', 'if', 'river', 'day', 'sea', 'heavy', 'other', 'wife', 'year', 'rope', 'wind', 'narrow', 'because', 'wet', 'salt', 'dirty', 'vomit', 'live', 'father', 'snake', 'husband', 'work', 'old', 'sister', 'mother', 'count', 'flower', 'dance', 'where', 'hunt', 'thin', 'wood', 'bad'})


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
