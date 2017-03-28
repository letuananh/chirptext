#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Demo code using chirptext
Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2015, Le Tuan Anh <tuananh.ke@gmail.com>
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

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2015, chirptext"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

#-----------------------------------------------------------------------

import os
import logging
from itertools import cycle

from chirptext import header, Counter, Timer, TextReport, Table, FileHelper
from chirptext.leutile import ChirpConfig as Cfg

DATA_DIR = FileHelper.abspath("data")
REPORT_LOC  = os.path.join(DATA_DIR, "foo.txt")
#-----------------------------------------------------------------------

def generate_report(report):
    report.header("A beautiful dummy report", level='h0')
    report.print("An introduction to the art of creating text report.")
    report.print(Cfg.LOREM_IPSUM)
    # a sample counter
    c = Counter()
    # demo sections & subsections
    for section in range(1,3):
        c.count('section')
        report.header("Section %s" % section, level='h1')
        report.print(Cfg.LOREM_IPSUM[:70])
        for subsect in range(1,3):
            c.count('subsection')
            report.header("Subsection %s" % subsect, level='h2')
            for k in range(1,4):
                report.print("Line %s" % k, level=1)
    # Demo draw table
    report.header('Summary Table')
    report.print("Here is a demo table", level=1)
    # Create a table
    tbl = Table()
    words = cycle(Cfg.LOREM_IPSUM.split())
    tbl.add_row(["Index", "Word #1", "Word #2", "Word #3", "Word #4"])
    for i in range(3):
        c.count('row')
        row = [i] + [next(words) for j in range(4)]
        tbl.add_row(row)
    # print the table to report file
    print_tbl = lambda x: report.print(x, level=1)
    tbl.print(print_func=print_tbl)
    # report statistics
    report.header("Data counter")
    c.summarise(report)
    # Done!
    report.close()

#-----------------------------------------------------------------------    
    
def main():
    header("Main method")
    c = Counter()
    t = Timer()
    
    t.start("Doing some time-consuming tasks ...")

    logging.info("Count even & odd numbers ...")
    for i in range(10000):
        if i % 2 == 0:
            c.count("even")
        else:
            c.count("odd")
    c.summarise()

    logging.info("Creating report dir ...")
    FileHelper.create_dir(DATA_DIR)

    report = TextReport(REPORT_LOC)
    logging.info("Now try to create a text report (Located at: %s)" % (report.get_path()))
    generate_report(report)

    # try to report to stdout
    logging.info("The same report to stdout ...")
    generate_report(TextReport())
    
    t.end("Done")

if __name__ == "__main__":
    main()
