# -*- coding: utf-8 -*-

'''
Readers for popular formats

Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
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

########################################################################

import os
import csv
import gzip
import codecs
import logging
import warnings

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

QUOTE_MINIMAL = csv.QUOTE_MINIMAL
QUOTE_NONE = csv.QUOTE_NONE
QUOTE_ALL = csv.QUOTE_ALL
__python_open = open


def getLogger():
    return logging.getLogger()


# -------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------

def to_string(content, encoding='utf-8'):
    if isinstance(content, bytes):
        return content.decode(encoding)
    elif isinstance(content, str):
        return content
    else:
        return str(content)


def is_file(path):
    ''' Check if path is a path to an existing file '''
    return path and os.path.isfile(to_string(path))


def open(path, encoding='utf-8', mode='rt', *args, **kwargs):
    if not mode:
        raise Exception("Invalid file access mode")
    elif mode in ('r', 'rt', 'rb') and not is_file(path):
        raise FileNotFoundError("File {} does not exist".format(path))
    # read or write
    if path.endswith('.gz'):
        if mode.endswith('b'):
            return gzip.open(path, mode=mode)
        else:
            return gzip.open(path, mode=mode, encoding=encoding)
    else:
        if mode.endswith('b'):
            return __python_open(path, mode=mode)
        else:
            return __python_open(path, mode=mode, encoding=encoding)


def process_file(path, processor, encoding='utf-8', mode='rt', *args, **kwargs):
    ''' Process a text file's content. If the file name ends with .gz, read it as gzip file '''
    if mode not in ('rt', 'rb', 'r'):
        raise Exception("Invalid file reading mode")
    with open(path, encoding=encoding, mode=mode, *args, **kwargs) as infile:
        return processor(infile)


def read_file(path, encoding='utf-8', *args, **kwargs):
    ''' Read text file content. If the file name ends with .gz, read it as gzip file.
    If mode argument is provided as 'rb', content will be read as byte stream.
    By default, content is read as string.
    '''
    if 'mode' in kwargs and kwargs['mode'] == 'rb':
        return process_file(path, processor=lambda x: x.read(),
                            encoding=encoding, *args, **kwargs)
    else:
        return process_file(path, processor=lambda x: to_string(x.read(), encoding),
                            encoding=encoding, *args, **kwargs)


def write_file(content, outpath, mode=None, encoding='utf-8'):
    ''' Write content to a file. If the path ends with .gz, gzip will be used. '''
    if not mode:
        if isinstance(content, bytes):
            mode = 'wb'
        else:
            mode = 'wt'
    if not outpath:
        raise ValueError("Output path is invalid")
    else:
        getLogger().debug("Writing content to {}".format(outpath))
        # convert content to string when writing text data
        if mode == 'wt' or mode == 'w' and not isinstance(content, str):
            content = to_string(content)
        elif mode == 'wb':
            # content needs to be encoded as bytes
            if not isinstance(content, str):
                content = to_string(content).encode(encoding)
            else:
                content = content.encode(encoding)
        if outpath.endswith('.gz'):
            with gzip.open(outpath, mode) as outfile:
                outfile.write(content)
        else:
            with open(outpath, mode=mode) as outfile:
                outfile.write(content)


def iter_csv_stream(input_stream, fieldnames=None, sniff=False, *args, **kwargs):
    ''' Read CSV content as a table (list of lists) from an input stream '''
    if 'dialect' not in kwargs and sniff:
        kwargs['dialect'] = csv.Sniffer().sniff(input_stream.read(1024))
        input_stream.seek(0)
    if 'quoting' in kwargs and kwargs['quoting'] is None:
        kwargs['quoting'] = csv.QUOTE_MINIMAL
    if fieldnames:
        # read csv using dictreader
        if isinstance(fieldnames, bool):
            reader = csv.DictReader(input_stream, *args, **kwargs)
        else:
            reader = csv.DictReader(input_stream, *args, fieldnames=fieldnames, **kwargs)
        for row in reader:
            yield row
    else:
        csvreader = csv.reader(input_stream, *args, **kwargs)
        for row in csvreader:
            yield row


def iter_tsv_stream(input_stream, *args, **kwargs):
    return iter_csv_stream(input_stream, *args, dialect='excel-tab', **kwargs)


def read_csv_iter(path, fieldnames=None, sniff=True, encoding='utf-8', *args, **kwargs):
    ''' Iterate through CSV rows in a file.
    By default, csv.reader() will be used any output will be a list of lists.
    If fieldnames is provided, DictReader will be used and output will be list of OrderedDict instead.
    CSV sniffing (dialect detection) is enabled by default, set sniff=False to switch it off.
    '''
    with open(path, mode='rt', encoding=encoding) as infile:
        for row in iter_csv_stream(infile, fieldnames=fieldnames, sniff=sniff, *args, **kwargs):
            yield row


def read_tsv_iter(path, *args, **kwargs):
    return read_csv_iter(path, *args, dialect='excel-tab', **kwargs)


def read_csv(path, fieldnames=None, sniff=True, encoding='utf-8', *args, **kwargs):
    ''' Read CSV rows as table from a file.
    By default, csv.reader() will be used any output will be a list of lists.
    If fieldnames is provided, DictReader will be used and output will be list of OrderedDict instead.
    CSV sniffing (dialect detection) is enabled by default, set sniff=False to switch it off.
    '''
    return list(r for r in read_csv_iter(path, fieldnames=fieldnames, sniff=sniff, encoding=encoding, *args, **kwargs))


def read_tsv(path, *args, **kwargs):
    return read_csv(path, dialect='excel-tab', *args, **kwargs)


def write_csv(path, rows, dialect='excel', fieldnames=None, quoting=csv.QUOTE_ALL, extrasaction='ignore', *args, **kwargs):
        ''' Write rows data to a CSV file (with or without fieldnames) '''
        if not quoting:
            quoting = csv.QUOTE_MINIMAL
        with open(path, mode='wt') as csvfile:
            if fieldnames:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect=dialect, quoting=quoting, extrasaction=extrasaction, *args, **kwargs)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
            else:
                writer = csv.writer(csvfile, dialect=dialect, quoting=quoting, *args, **kwargs)
                for row in rows:
                    writer.writerow(row)


def write_tsv(path, rows, *args, **kwargs):
    return write_csv(path, rows, dialect='excel-tab', *args, **kwargs)


class CSV(object):

    QUOTE_MINIMAL = csv.QUOTE_MINIMAL
    QUOTE_NONE = csv.QUOTE_NONE
    QUOTE_ALL = csv.QUOTE_ALL

    @staticmethod
    def read(file_name, header=False, *args, **kwargs):
        warnings.warn("chirptext.io.CSV is deprecated and will be removed in near future.", DeprecationWarning)
        return read_csv(file_name, fieldnames=header, *args, **kwargs)

    @staticmethod
    def read_tsv(file_name, *args, **kwargs):
        warnings.warn("chirptext.io.CSV is deprecated and will be removed in near future.", DeprecationWarning)
        return read_tsv(file_name, *args, **kwargs)

    @staticmethod
    def write(file_name, rows, header=None, *args, **kwargs):
        ''' Write rows data to a CSV file (with or without header) '''
        warnings.warn("chirptext.io.CSV is deprecated and will be removed in near future.", DeprecationWarning)
        write_csv(file_name, rows, fieldnames=header, *args, **kwargs)

    @staticmethod
    def write_tsv(file_name, rows, *args, **kwargs):
        warnings.warn("chirptext.io.CSV is deprecated and will be removed in near future.", DeprecationWarning)
        write_tsv(file_name, rows, *args, **kwargs)
