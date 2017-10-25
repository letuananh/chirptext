# -*- coding: utf-8 -*-

'''
Readers for popular formats
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
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

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
import csv
import logging
from collections import defaultdict as dd
from collections import namedtuple

from .leutile import FileHelper

#-------------------------------------------------------------------------------
# CONFIGURATION
#-------------------------------------------------------------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#-------------------------------------------------------------------------------
# DATA STRUCTURES
#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------
# FUNCTIONS
#-------------------------------------------------------------------------------

class CSV(object):

    QUOTE_MINIMAL = csv.QUOTE_MINIMAL
    QUOTE_NONE = csv.QUOTE_NONE
    QUOTE_ALL = csv.QUOTE_ALL

    @staticmethod
    def read(file_name, dialect=None, header=False):
        with open(file_name, newline='') as csvfile:
            if not dialect:
                # auto detect
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
            if not header:
                reader = csv.reader(csvfile, dialect=dialect)
                return list(reader)
            else:
                reader = csv.DictReader(csvfile, dialect=dialect)
                return list(reader)

    @staticmethod
    def write(file_name, rows, dialect='excel', header=None, quoting=csv.QUOTE_ALL, extrasaction='ignore'):
        ''' Write rows data to a CSV file (with or without header) '''
        if not quoting:
            quoting = csv.QUOTE_MINIMAL
        with open(file_name, 'w') as csvfile:
            if not header:
                writer = csv.writer(csvfile, dialect=dialect, quoting=quoting)
                for row in rows:
                    writer.writerow(row)
            else:
                writer = csv.DictWriter(csvfile, dialect=dialect, fieldnames=header, quoting=quoting, extrasaction=extrasaction)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

    @staticmethod
    def write_tsv(file_name, rows, quoting=csv.QUOTE_ALL, **kwargs):
        CSV.write(file_name, rows, dialect='excel-tab', quoting=quoting, **kwargs)


#-------------------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    print("This is a library, not an application")
