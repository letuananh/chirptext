#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-

'''
Chirp Tools
Latest version can be found at https://github.com/letuananh/chirptext

References:
    Python documentation:
        https://docs.python.org/
    PEP 0008 - Style Guide for Python Code
        https://www.python.org/dev/peps/pep-0008/
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
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

__author__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2017, chirptext"
__license__ = "MIT"
__maintainer__ = "Le Tuan Anh"
__version__ = "0.1"
__status__ = "Prototype"
__credits__ = []

########################################################################

import os
import codecs
import textwrap

from chirptext import __version_long__
from chirptext import Counter, TextReport
from chirptext.cli import CLIApp, setup_logging

# -------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------

setup_logging('logging.json', 'logs')


# -------------------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------------------

def gen_vocab(cli, args):
    ''' Generate vocabulary list from a tokenized file '''
    if args.topk and args.topk <= 0:
        topk = None
        cli.logger.warning("Invalid k will be ignored (k should be greater than or equal to 1)")
    else:
        topk = args.topk
    if args.stopwords:
        with open(args.stopwords, 'r') as swfile:
            stopwords = swfile.read().splitlines()
    else:
        stopwords = []
    if os.path.isfile(args.input):
        cli.logger.info("Generating vocabulary list from file {}".format(args.input))
        with codecs.open(args.input, encoding='utf-8') as infile:
            if args.output:
                cli.logger.info("Output: {}".format(args.output))
            rp = TextReport(args.output)
            lines = infile.read().splitlines()
            c = Counter()
            for line in lines:
                words = line.split()
                c.update(w for w in words if w not in stopwords)
            # report vocab
            word_freq = c.most_common(topk)
            words = [k for k, v in word_freq]
            rp.header("Lexicon")
            rp.writeline("\n".join(textwrap.wrap(" ".join(w for w in words), width=70)))
            for k, v in word_freq:
                rp.print("{}: {}".format(k, v))
    else:
        cli.logger.warning("File {} does not exist".format(args.input))


def show_version(cli, args):
    print("Chirptext toolkit - Version {}".format(__version_long__))


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

def main():
    ''' ChirpText Tools main function '''
    app = CLIApp(desc='ChirpText Tools', logger=__name__, show_version=show_version)
    # add tasks
    vocab_task = app.add_task('vocab', func=gen_vocab)
    vocab_task.add_argument('input', help='Input file')
    vocab_task.add_argument('--output', help='Output file', default=None)
    vocab_task.add_argument('--stopwords', help='Stop word to ignore', default=None)
    vocab_task.add_argument('-k', '--topk', help='Only select the top k frequent elements', default=None, type=int)
    # run app
    app.run()


if __name__ == "__main__":
    main()
