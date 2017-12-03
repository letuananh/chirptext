# -*- coding: utf-8 -*-

# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>

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

import os
import codecs
import logging
import sys
import time
import errno
from collections import Counter as PythonCounter
from collections import OrderedDict

if sys.version_info >= (3, 0):
    from itertools import zip_longest
else:
    from itertools import izip_longest


# -------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


LOREM_IPSUM = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."


###############################################################################

def confirm(msg):
    return input(msg).upper() in ['Y', 'YES', 'OK']


def uniquify(a_list):
    return list(OrderedDict(zip(a_list, range(len(a_list)))).keys())


def header(*msg, level='h1', separator=" ", print_out=print):
    ''' Print header block in text mode
    '''
    out_string = separator.join(str(x) for x in msg)
    if level == 'h0':
        # box_len = 80 if len(msg) < 80 else len(msg)
        box_len = 80
        print_out('+' + '-' * (box_len + 2))
        print_out("| %s" % out_string)
        print_out('+' + '-' * (box_len + 2))
    elif level == 'h1':
        print_out("")
        print_out(out_string)
        print_out('-' * 60)
    elif level == 'h2':
        print_out('\t%s' % out_string)
        print_out('\t' + ('-' * 40))
    else:
        print_out('\t\t%s' % out_string)
        print_out('\t\t' + ('-' * 20))


def is_number(s):
    ''' Check if something is a number
    '''
    try:
        if str(float(s)) != 'nan':
            return True
    except Exception:
        pass
    return False


if sys.version_info >= (3, 0):
    def grouper(iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return zip_longest(fillvalue=fillvalue, *args)
else:
    def grouper(iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return izip_longest(fillvalue=fillvalue, *args)

###############################################################################


class TextReport:

    STDOUT = '*stdout*'

    ''' Helper for creating text report with indentation, tables and flexible output (to stdout or a file)
    '''
    def __init__(self, report_path=None, mode='w', name=None, auto_flush=True, encoding='utf8'):
        ''' Create a text report.

        Arguments:
            report_path -- Path to report file
            mode        -- a for append, w (default) for create from scratch (overwrite existing file)
        '''
        if not report_path or report_path == TextReport.STDOUT:
            self.report_path = TextReport.STDOUT
            self.report_file = sys.stdout
            self.name = 'stdout'
            self.mode = None
            self.auto_flush = False
            pass
        else:
            self.report_path = os.path.expanduser(report_path)
            self.report_file = open(self.report_path, mode, encoding=encoding)
            self.name = name if name else FileHelper.getfilename(self.report_path)
            self.auto_flush = auto_flush
            self.mode = mode
        self.print = self.writeline  # just an alias

    @property
    def closed(self):
        return self.report_file is None or self.report_file.closed

    def write(self, *msg, separator=" ", level=0):
        out_string = separator.join(str(x) for x in msg)
        self.report_file.write("\t" * level)
        self.report_file.write(out_string)
        if self.auto_flush:
            self.report_file.flush()

    def writeline(self, *msg, level=0):
        msg = msg + ('\n',)
        self.write(*msg, level=level)

    def header(self, *msg, **kwargs):
        header(*msg, print_out=self.writeline, **kwargs)

    def close(self):
        if self.mode and self.report_file != sys.stdout:
            try:
                self.report_file.flush()
                self.report_file.close()
                self.report_file = None
            except Exception as e:
                getLogger().exception("Error raised while saving report")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_path(self):
        return self.report_path

    @staticmethod
    def null():
        ''' Get a dev null report (print to nowhere)'''
        return TextReport('/dev/null')


###############################################################################


class Timer:
    ''' Measure tasks' runtime
    '''
    def __init__(self, logger=None, report=None):
        self.start_time = time.time()
        self.end_time = time.time()
        self.__logger = logger
        self.__report = report
        self.end = self.stop  # just an alias

    @property
    def logger(self):
        return self.__logger if self.__logger is not None else getLogger()

    def exec_time(self):
        ''' Calculate run time '''
        return self.end_time - self.start_time

    def log(self, action, desc=None):
        msg = '{action} - [{note}]'.format(action, desc) if desc else action
        self.logger.info(msg)
        if self.report:
            self.report.writeline(msg)
        return self

    def start(self, desc=''):
        self.log("Started", desc=desc)
        self.start_time = time.time()
        return self

    def stop(self, desc=''):
        self.end_time = time.time()
        msg = "[{} | {}]".format(desc, str(self)) if desc else str(self)
        self.log("Stopped", desc=msg)
        return self

    def __str__(self):
        return "Execution time: %.2f sec(s)" % (self.exec_time(),)


###############################################################################

class Counter(PythonCounter):
    ''' Powerful counter class
    '''
    def __init__(self, priority=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__priority = priority if priority else []

    def count(self, key):
        self.update({key: 1})

    @property
    def priority(self):
        return list(self.__priority)

    @priority.setter
    def priority(self, priority):
        self.priority = list(priority)

    def get_report_order(self):
        ''' Keys are sorted based on report order (i.e. some keys to be shown first)
            Related: see sorted_by_count
        '''
        order_list = []
        for x in self.__priority:
            order_list.append([x, self[x]])
        for x in sorted(list(self.count_map.keys())):
            if x not in self.__priority:
                order_list.append([x, self[x]])
        return order_list

    def summarise(self, report=None, byfreq=True):
        if not report:
            report = TextReport()
        for k, v in self.get_report_order():
            report.writeline("%s: %d" % (k, v))

    def save(self, file_loc):
        '''Save counter information to files'''
        with open(file_loc, 'w') as outfile:
            for k, v in self.get_report_order():
                outfile.write("%s: %d\n" % (k, v))

    def sorted_by_count(self, top_k=None):
        ''' Return a list of 2-element arrays that are sorted by count in descending order
            E.g. (['label1', 23], ['label2', 5])
            :deprecated: This function will be removed in the future
        '''
        return self.most_common(top_k)

    def group_by_count(self):
        d = OrderedDict()
        for item, count in self.most_common():
            if count not in d:
                d[count] = []
            d[count].append(item)
        return d.items()


class StringTool:
    ''' Common string function
    '''
    @staticmethod
    def strip(a_str):
        return a_str.strip() if a_str else ''

    @staticmethod
    def to_str(a_str):
        return str(a_str) if a_str else ''

    @staticmethod
    def detokenize(tokens):
        sentence_text = ' '.join(tokens)
        sentence_text = sentence_text.replace(" , , ", ", ")
        sentence_text = sentence_text.replace(' , ', ', ').replace('“ ', '“').replace(' ”', '”')
        sentence_text = sentence_text.replace(' ! ', '! ').replace(" 'll ", "'ll ").replace(" 've ", "'ve ").replace(" 're ", "'re ").replace(" 'd ", "'d ")
        sentence_text = sentence_text.replace(" 's ", "'s ")
        sentence_text = sentence_text.replace(" 'm ", "'m ")
        sentence_text = sentence_text.replace(" ' ", "' ")
        sentence_text = sentence_text.replace(" ; ", "; ")
        sentence_text = sentence_text.replace(" : ", ": ")
        sentence_text = sentence_text.replace("( ", "(")
        sentence_text = sentence_text.replace(" )", ")")
        sentence_text = sentence_text.replace(" ?", "?")
        sentence_text = sentence_text.replace(" n't ", "n't ")
        sentence_text = sentence_text.replace("  ", " ")
        sentence_text = sentence_text.replace('``', "“").replace("''", "”")
        sentence_text = sentence_text.replace("“ ", "“").replace(" ”", "”")
        if sentence_text[-2:] in (' .', ' :', ' ?', ' !', " ;"):
            sentence_text = sentence_text[:-2] + sentence_text[-1]
        sentence_text = sentence_text.strip()
        return sentence_text


###############################################################################

class FileHub:
    ''' A helper class for working with multiple text reports at the same time
    '''
    def __init__(self, *filenames, working_dir='.', default_mode='a', ext='txt'):
        self.files = {}
        self.ext = ext if ext else ''
        self.default_mode = default_mode

    def __getitem__(self, key):
        if key not in self.files:
            self.open(key)
        return self.files[key]

    def __setitem__(self, key, value):
        self.files[key] = value

    def get_path(self, key):
        if os.path.isabs(key):
            return key
        else:
            return os.path.join(self.working_dir, key + '.' + self.ext)

    def open(self, key, mode=None, **kwargs):
        if not mode:
            mode = self.default_mode
        self.files[key] = TextReport(self.get_path(key), mode=mode, **kwargs)
        return self.files[key]

    def close(self):
        for key in self.files.keys():
            self[key].close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


###############################################################################

class Table:
    ''' A text-based table which can be used with TextReport
    '''
    def __init__(self, header=True, padding=True, NoneValue=None):
        self.rows = []
        self.col_count = 0
        self.NoneValue = NoneValue
        self.max_lengths = []
        self.header = header
        self.padding = padding

    def maxlength(self, val_a, val_b):
        len_a = len(val_a) if val_a else 0
        len_b = len(val_b) if val_b else 0
        return len_a if len_a > len_b else len_b

    def add_row(self, new_row):
        if new_row is None:
            raise ValueError("Row cannot be None")
        if len(new_row) > self.col_count:
            self.col_count = len(new_row)  # longer row
            for row in self.rows:
                # add cell
                row += [self.NoneValue] * (len(new_row) - self.col_count)
        elif len(new_row) < self.col_count:
            new_row += [self.NoneValue] * (self.col_count - len(new_row))
        self.rows.append(list(new_row))  # clone a list, rather than store the ref passed in

    def __getitem__(self, row_id):
        return list(self.rows[row_id])    # clone a row to return

    def get_column(self, col_id):
        return [x[col_id] if x[col_id] is not None else self.NoneValue for x in self.rows]

    def format(self):
        ''' Format table to print out
        '''
        self.max_lengths = []
        for row in self.rows:
            if len(self.max_lengths) < len(row):
                self.max_lengths += [0] * (len(row) - len(self.max_lengths))
            for idx, val in enumerate(row):
                len_cell = len(str(val)) if val else 0
                if self.max_lengths[idx] < len_cell:
                    self.max_lengths[idx] = len_cell
        return self.max_lengths

    def print_separator(self, print_func):
        self.print_cells(['-' * (x + (2 if self.padding else 0)) for x in self.max_lengths], print_func, joint='+')

    def print_cells(self, cells, print_func=print, extra_lines=False, joint='|'):
        print_func(joint + joint.join(cells) + joint)
        if extra_lines:
            self.print_separator(print_func)

    def print(self, print_func=print):
        max_lengths = self.format()
        self.print_separator(print_func)
        for ridx, row in enumerate(self.rows):
            cells = []
            for idx, cell in enumerate(row):
                txt = str(cell)
                cell_width = max_lengths[idx]
                if ridx == 0 and self.header:
                    txt = txt.center(cell_width)
                else:
                    txt = txt.rjust(cell_width) if is_number(txt) else txt.ljust(cell_width)
                if self.padding:
                    txt = ' ' + txt + ' '
                cells.append(txt)
            self.print_cells(cells, print_func, extra_lines=(self.header and ridx == 0))
        self.print_separator(print_func)


###############################################################################

class FileHelper:
    @staticmethod
    def getfilename(file_path):
        ''' Get filename without extension
        '''
        return os.path.splitext(FileHelper.getfullfilename(file_path))[0]

    @staticmethod
    def getfullfilename(file_path):
        ''' Get full filename (with extension)
        '''
        if file_path:
            return os.path.basename(file_path)
        else:
            return ''

    @staticmethod
    def abspath(a_path):
        return os.path.abspath(os.path.expanduser(a_path))

    @staticmethod
    def create_dir(dir_path):
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except Exception as e:
                getLogger().exception("Cannot create folder [%s]" % (dir_path,))
                raise

    @staticmethod
    def get_child_folders(path):
        ''' Get all child folders of a folder '''
        path = FileHelper.abspath(path)
        return [dirname for dirname in os.listdir(path) if os.path.isdir(os.path.join(path, dirname))]

    @staticmethod
    def get_child_files(path):
        ''' Get all child files of a folder '''
        path = FileHelper.abspath(path)
        return [filename for filename in os.listdir(path) if os.path.isfile(os.path.join(path, filename))]

    @staticmethod
    def remove_file(filepath):
        ''' Delete a file '''
        try:
            os.remove(os.path.abspath(os.path.expanduser(filepath)))
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @staticmethod
    def save(path, content):
        try:
            with open(os.path.abspath(os.path.expanduser(path)), "wb") as local_file:
                if isinstance(content, str):
                    local_file.write(bytes(content, 'UTF-8'))
                else:
                    local_file.write(content)
            return True
        except Exception as e:
            getLogger().debug("Error while saving content to {file}\r\n{e}".format(file=path, e=e))
        return False

    @staticmethod
    def read(a_file, mode='r'):
        with open(a_file, mode=mode) as fileobj:
            return fileobj.read()


# TODO: Should we switch to JSON?
class ConfigFile:

    def __init__(self, filename, splitter='='):
        self.filename = os.path.abspath(os.path.expanduser(filename))
        self.splitter = splitter

    def read(self):
        ''' If the file does not exist, this function will return an empty dictionary
        '''
        kvdict = {}
        if not os.path.isfile(self.filename):
            return kvdict
        with codecs.open(self.filename, 'r', encoding='utf-8') as fileobj:
            for line in fileobj.readlines():
                line = line.strip()
                if line.startswith('#') or len(line) == 0:
                    continue
                else:
                    k, v = line.split(self.splitter, 1)
                    kvdict[k] = v
            return kvdict
