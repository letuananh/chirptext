#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing leutile

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import logging
import unittest
from pathlib import Path

from chirptext.leutile import Counter, TextReport, StringTool, LOREM_IPSUM, Timer, piter
from chirptext.leutile import FileHelper
from chirptext.leutile import AppConfig


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

TEST_DATA = os.path.join(os.path.dirname(__file__), 'data')


def getLogger():
    return logging.getLogger(__name__)


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

    def test_piter(self):
        p1 = piter(range(5))
        l1 = [(x, p1.peep().value if p1.peep() else None) for x in p1]
        self.assertEqual(l1, [(0, 1), (1, 2), (2, 3), (3, 4), (4, None)])
        # empty list
        p2 = piter([])
        self.assertRaises(StopIteration, lambda: next(p2))
        self.assertIsNone(p2.current())
        self.assertIsNone(p2.peep())
        # 1 element iteration
        p3 = piter([1])
        v = next(p3)
        self.assertEqual(v, 1)
        self.assertIsNone(p3.peep())
        self.assertRaises(Exception, lambda: piter(None))
        # simple parser
        lssv = "src: me\ntxt:It works\n\nsrc:him\ntxt:It rains\ncmt:I made it up\n\nsrc:anonymous\ntxt:cow level is real"
        groups = []
        current = []
        p = piter(lssv.splitlines())
        for l in p:
            if l:
                current.append(l)
            if not l or not p.peep():
                if current:
                    groups.append(current)
                    current = []
        self.assertEqual(groups, [['src: me', 'txt:It works'], ['src:him', 'txt:It rains', 'cmt:I made it up'], ['src:anonymous', 'txt:cow level is real']])

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
        top5chars = {(char, count) for char, count in ct.most_common(5)}
        expected = {('o', 29), ('e', 37), ('a', 29), ('t', 32), ('i', 42)}
        for k, v in ct.most_common(5):
            getLogger().debug("{}: {}".format(k, v))
        self.assertEqual(top5chars, expected)

    def test_textreport(self):
        with TextReport.null() as rp:
            rp.writeline("null")
            rp.writeline(123)
            self.assertEqual(rp.content(), '')
        with TextReport() as rp:
            rp.writeline("Test writing to stdout ...")
            rp.writeline("multiple line output", 123)
            self.assertEqual(rp.content(), '')
        with TextReport(os.path.join(TEST_DATA, "del.me")) as rp:
            rp.writeline("ABC")
            rp.writeline(123)
            self.assertEqual(rp.content(), '')
        self.assertTrue(rp.closed)
        # test string report
        with TextReport.string() as rp:
            rp.writeline("ABC")
            rp.writeline(123, 456, 789)
            self.assertEqual(rp.content(), 'ABC\n123 456 789\n')

    def test_timer(self):
        rp = TextReport.string()
        t = Timer(report=rp)
        msg = "Do something expensive"
        t.start(msg)
        do_expensive()
        t.stop(msg)
        getLogger().debug(rp.content())
        self.assertIn("Started", rp.content())
        self.assertIn("Stopped", rp.content())
        # test do()
        rp = TextReport.string()
        t = Timer(report=rp)
        t.do(lambda: do_expensive(), desc=msg)
        self.assertIn("Started", rp.content())
        self.assertIn("Stopped", rp.content())
        getLogger().debug(rp.content())


def do_expensive(n=10000):
    s = TextReport.string()
    for i in range(n):
        s.print("This is string number #{}".format(i))
    return str(s.content())


class TestFileHelper(unittest.TestCase):

    def test_replace_ext(self):
        self.assertEqual(Path(FileHelper.replace_ext('../data/foo.xml', 'json')).as_posix(),
                         '../data/foo.json')
        self.assertEqual(Path(FileHelper.replace_ext('../data/foo', 'json')).as_posix(),
                         '../data/foo.json')
        self.assertEqual(Path(FileHelper.replace_ext('../data/foo.xml', '')).as_posix(),
                         '../data/foo')
        self.assertEqual(Path(FileHelper.replace_ext('../data/foo.xml', None)).as_posix(),
                         '../data/foo')
        self.assertRaises(Exception, lambda: FileHelper.replace_ext(None, None))
        self.assertRaises(Exception, lambda: FileHelper.replace_ext('', None))
        self.assertRaises(Exception, lambda: FileHelper.replace_ext((1, 2, 3, 4), None))

    def test_rename(self):
        self.assertEqual(Path(FileHelper.replace_name('/data/foo.xml', 'bar')),
                         Path('/data/bar.xml'))
        self.assertEqual(Path(FileHelper.replace_name('../data/foo', 'bar')),
                         Path('../data/bar'))
        self.assertEqual(Path(FileHelper.replace_name('../foo.xml', 'bar')),
                         Path('../bar.xml'))
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
        expected = ['./.foo', './.foo.json', './foo', './foo.json', './data/foo', './data/foo.json', './data/.foo', './data/.foo.json', '~/.foo', '~/.foo.json', '~/.foo/config', '~/.foo.json/config', '~/.foo/config.json', '~/.foo.json/config.json', '~/.config/foo', '~/.config/foo.json', '~/.config/.foo', '~/.config/.foo.json', '~/.config/foo/config', '~/.config/foo.json/config', '~/.config/foo/config.json', '~/.config/foo.json/config.json', '~/.config/foo/foo', '~/.config/foo.json/foo.json']
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
