#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing leutile

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
import unittest

from chirptext.leutile import Counter, TextReport, StringTool, LOREM_IPSUM
from chirptext.leutile import FileHelper
from chirptext.leutile import AppConfig


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

class TestLeUtile(unittest.TestCase):

    def test_string_tool(self):
        self.assertEqual(StringTool.strip(None), '')
        self.assertEqual(StringTool.strip(' '), '')
        self.assertEqual(StringTool.to_str(None), '')
        # detokenize
        words = ["I", "'ll", "go", "home", "."]
        self.assertEqual(StringTool.detokenize(words), "I'll go home.")
        self.assertEqual(StringTool.detokenize(["This", "(", "thing", ")", "is", "a", "comment", "!"]), "This (thing) is a comment!")
        self.assertEqual(StringTool.detokenize("He said `` why ? '' .".split()), "He said “why?”.")
        self.assertEqual(StringTool.detokenize("Where are you ?".split()), "Where are you?")
        self.assertEqual(StringTool.detokenize("Note : It works .".split()), "Note: It works.")
        self.assertEqual(StringTool.detokenize("( A ) ; ".split()), "(A);")
        self.assertEqual(StringTool.detokenize("( A ) ; B ".split()), "(A); B")

    def test_counter(self):
        print("Test counter")
        c = Counter()
        c.count("A")
        c.count(None)
        c.count(None)
        self.assertEqual(c['A'], 1)
        self.assertEqual(c[None], 2)
        self.assertEqual(c.most_common(), [(None, 2), ('A', 1)])
        ct = Counter()
        for char in LOREM_IPSUM:
            if char == ' ':
                continue
            ct.count(char)
        top5chars = [char for char, count in ct.most_common(5)]
        self.assertEqual(top5chars, ['i', 'e', 't', 'o', 'a'])

    def test_textreport(self):
        with TextReport.null() as rp:
            rp.writeline("null")
            rp.writeline(123)
            self.assertEqual(rp.content(), '')
        with TextReport() as rp:
            rp.writeline("stdout")
            rp.writeline(123)
            self.assertEqual(rp.content(), '')
        with TextReport("/tmp/del.me") as rp:
            rp.writeline("ABC")
            rp.writeline(123)
            self.assertEqual(rp.content(), '')
        self.assertTrue(rp.closed)
        # test string report
        with TextReport.string() as rp:
            rp.writeline("ABC")
            rp.writeline(123, 456, 789)
            self.assertEqual(rp.content(), 'ABC \n123 456 789 \n')


class TestFileHelper(unittest.TestCase):

    def test_replace_ext(self):
        self.assertEqual(FileHelper.replace_ext('../data/foo.xml', 'json'),
                         '../data/foo.json')
        self.assertEqual(FileHelper.replace_ext('../data/foo', 'json'),
                         '../data/foo.json')
        self.assertEqual(FileHelper.replace_ext('../data/foo.xml', ''),
                         '../data/foo')
        self.assertEqual(FileHelper.replace_ext('../data/foo.xml', None),
                         '../data/foo')
        self.assertRaises(Exception, lambda: FileHelper.replace_ext(None, None))
        self.assertRaises(Exception, lambda: FileHelper.replace_ext('', None))
        self.assertRaises(Exception, lambda: FileHelper.replace_ext((1, 2, 3, 4), None))

    def test_rename(self):
        self.assertEqual(FileHelper.replace_name('/data/foo.xml', 'bar'),
                         '/data/bar.xml')
        self.assertEqual(FileHelper.replace_name('../data/foo', 'bar'),
                         '../data/bar')
        self.assertEqual(FileHelper.replace_name('../foo.xml', 'bar'),
                         '../bar.xml')
        self.assertRaises(Exception, lambda: FileHelper.replace_name(None, None))
        self.assertRaises(Exception, lambda: FileHelper.replace_name('', None))
        self.assertRaises(Exception, lambda: FileHelper.replace_name((1, 2, 3, 4), None))
        self.assertRaises(Exception, lambda: FileHelper.replace_name("/usr/foo", None))
        self.assertRaises(Exception, lambda: FileHelper.replace_name("/usr/foo", ''))
        self.assertRaises(Exception, lambda: FileHelper.replace_name("/usr/foo", (1, 2, 3)))


class TestConfigFile(unittest.TestCase):

    def test_locate_config_file(self):
        cfg = AppConfig(name='foo', mode=AppConfig.JSON)
        actual = cfg.potentials()
        expected = ['./.foo', './foo', './data/foo', './data/.foo', '~/.foo', '~/.foo/config',
                    '~/.config/foo', '~/.config/.foo', '~/.config/foo/config', '~/.config/foo/foo']
        self.assertEqual(actual, expected)
        # default mode is INI
        cfg_ini = AppConfig('chirptest', working_dir=os.path.dirname(__file__))
        self.assertEqual(cfg_ini.config.sections(), ['AUTHOR'])
        self.assertEqual(cfg_ini.config['DEFAULT']['package'], 'chirptext.test')
        self.assertEqual(cfg_ini.config['DEFAULT']['tester'], 'unittest')
        self.assertEqual(cfg_ini.config['AUTHOR']['name'], 'Le Tuan Anh')
        self.assertEqual(cfg_ini.config['AUTHOR']['tester'], 'unittest')
        self.assertEqual(cfg_ini.config.get('AUTHOR', 'desc', fallback='nothing'), 'nothing')
        # test writing config
        with TextReport.string() as strfile:
            cfg_ini.config['AUTHOR']['desc'] = 'An author'
            cfg_ini.config.write(strfile.file)
            self.assertIn('desc = An author', strfile.content())
        # use JSON


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
