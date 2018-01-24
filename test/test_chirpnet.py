#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing chirpnet lib

Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

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
import unittest

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

class TestMain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.isdir(TEST_DATA):
            getLogger().info("Creating TEST DATA folder at {}".format(TEST_DATA))
            FileHelper.create_dir(TEST_DATA)

    def test_chirpnet(self):
        print("Test WebHelper")
        web = WebHelper(cache=JiCache(TEST_CACHE))
        u = "https://letuananh.github.io/test/data.json"
        data = web.fetch(u, encoding="utf-8")
        self.assertEqual(data.strip(), '{ "name": "Kungfu Panda" }')
        self.assertIn(u, web.cache)


########################################################################

if __name__ == "__main__":
    unittest.main()
