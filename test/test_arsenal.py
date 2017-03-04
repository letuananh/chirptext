#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing arsenal lib
Latest version can be found at https://github.com/letuananh/chirptext

References:
    Python documentation:
        https://docs.python.org/
    Python unittest
        https://docs.python.org/3/library/unittest.html
    --
    argparse module:
        https://docs.python.org/3/howto/argparse.html
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

#Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>

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

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2017, chirptext"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import os
import logging
import unittest

from chirptext.leutile import ChirpConfig as CC
from chirptext import JiCache

#----------------------------------------------------------------------
# Configuration
#----------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
TEST_DIR = os.path.dirname(__file__)
TEST_CACHE = os.path.join(TEST_DIR, 'test_cache.db')


########################################################################

class TestMain(unittest.TestCase):

    def try_cache(self, cache, key, value):
        if key in cache:
            cache.delete_blob(key)
        cache.insert_string(key, value)
        self.assertIn(key, cache)
        self.assertEqual(cache.retrieve_string(key), value)

    def test_empty_cache(self):
        TEST_CACHE2 = os.path.join(TEST_DIR, 'test_cache2.db')
        JiCache(TEST_CACHE2)
        self.assertFalse(os.path.exists(TEST_CACHE2))

    def test_arsenal(self):
        print("Test JiCache")
        cache = JiCache(TEST_CACHE)
        # test insert blob
        self.try_cache(cache, 'lorem', CC.LOREM_IPSUM)
        self.try_cache(cache, 1, 'Key is a number')
        self.try_cache(cache, None, 'None key')


########################################################################

def main():
    unittest.main()


if __name__ == "__main__":
    main()
