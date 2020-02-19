#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing arsenal lib

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import logging
import unittest

from chirptext.leutile import LOREM_IPSUM
from chirptext import JiCache

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

TEST_DIR = os.path.dirname(__file__)
TEST_CACHE = os.path.join(TEST_DIR, 'data', 'test_cache.db')


def getLogger():
    return logging.getLogger(__name__)


########################################################################

class TestArsenal(unittest.TestCase):

    def try_cache(self, cache, key, value):
        # delete the blob if it exists
        if key in cache:
            getLogger().debug("Deleting blob with key = {}".format(key))
            cache.delete_blob(key)
        # make sure that it is not there anymore
        self.assertNotIn(key, cache)
        cache.insert_string(key, value)
        # make sure that it is inserted
        self.assertIn(key, cache)
        # make sure that the content is the same
        self.assertEqual(cache.retrieve_string(key), value)

    def test_empty_cache(self):
        TEST_CACHE2 = os.path.join(TEST_DIR, 'test_cache2.db')
        JiCache(TEST_CACHE2)
        self.assertFalse(os.path.exists(TEST_CACHE2))

    def test_arsenal(self):
        print("Test arsenal module")
        cache = JiCache(TEST_CACHE)
        # test insert blob
        self.try_cache(cache, 'lorem', LOREM_IPSUM)
        self.try_cache(cache, 1, 'Key is a number')
        self.try_cache(cache, None, 'None key')


########################################################################

if __name__ == "__main__":
    unittest.main()
