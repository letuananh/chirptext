#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing chirpnet lib

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import logging
import unittest
from pathlib import Path

from chirptext import JiCache, WebHelper, FileHelper

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
TEST_CACHE = os.path.join(TEST_DATA, 'test_cache.db')


def getLogger():
    return logging.getLogger(__name__)


########################################################################

class TestChirpnet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.isdir(TEST_DATA):
            getLogger().info("Creating TEST DATA folder at {}".format(TEST_DATA))
            FileHelper.create_dir(TEST_DATA)

    def test_chirpnet(self):
        print("Test WebHelper")
        # explicit cache
        web = WebHelper(cache=JiCache(TEST_CACHE))
        u = "https://letuananh.github.io/test/data.json"
        data = web.fetch(u, encoding="utf-8")
        self.assertEqual(data.strip(), '{ "name": "Kungfu Panda" }')
        self.assertIn(u, web.cache)
        # how about just a path as string?
        web2 = WebHelper(TEST_CACHE)
        self.assertIn(u, web2.cache)
        # test path object
        web3 = WebHelper(Path(TEST_CACHE))
        self.assertIn(u, web3.cache)
        # no cache
        web_nocache = WebHelper()
        self.assertIsNone(web_nocache.cache)
        web_nocache = WebHelper(None)
        self.assertIsNone(web_nocache.cache)

    def test_fetch_json(self):
        web = WebHelper(TEST_CACHE)
        u = "https://letuananh.github.io/test/data.json"
        data = web.fetch_json(u, encoding="utf-8")
        # it must be json
        self.assertEqual(data, {"name": "Kungfu Panda"})
        # test fetch non existent URL
        u_error = "https://letuananh.github.io/test/data-null.json"
        print("Fetch nonexistent url ... default quiet=True")
        data = web.fetch_json(u_error, encoding="utf-8")
        self.assertIsNone(data)
        # must raise exception if not quiet
        print("Fetch nonexistent url with quiet=False")
        self.assertRaises(Exception, lambda: web.fetch_json(u_error, encoding="utf-8", quiet=False))


########################################################################

if __name__ == "__main__":
    unittest.main()
