# -*- coding: utf-8 -*-

''' Miscellaneous tools for text processing

Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT

'''

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
import io
import logging
import sys
import time
import errno
import json
import configparser
from collections import Counter as PythonCounter
from collections import OrderedDict

from itertools import zip_longest


# -------------------------------------------------------------------------------
# Configuration
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


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


###############################################################################

class Counter(PythonCounter):
    ''' Powerful counter class
    '''
    def __init__(self, priority=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__priority = priority if priority else []

    def count(self, key):
        self.update({key})

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
        for x in sorted(list(self.keys())):
            if x not in self.__priority:
                order_list.append([x, self[x]])
        return order_list

    def summarise(self, report=None, byfreq=True, limit=None):
        if not report:
            report = TextReport()
        items = self.most_common() if byfreq else self.get_report_order()
        if limit:
            items = items[:limit]
        for k, v in items:
            report.writeline("%s: %d" % (k, v))

    def group_by_count(self):
        d = OrderedDict()
        for item, count in self.most_common():
            if count not in d:
                d[count] = []
            d[count].append(item)
        return d.items()


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
        msg = '{action} - [{desc}]'.format(action=action, desc=desc) if desc else action
        self.logger.info(msg)
        if self.__report:
            self.__report.writeline(msg)
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

    def do(self, task, desc=''):
        self.start(desc)
        task()
        self.stop(desc)

    def __str__(self):
        return "Execution time: %.2f sec(s)" % (self.exec_time(),)


###############################################################################

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

class TextReport:

    STDOUT = '*stdout*'
    STRINGIO = '*string*'

    ''' Helper for creating text report with indentation, tables and flexible output (to stdout or a file)
    '''
    def __init__(self, path=None, mode='w', name=None, auto_flush=True, encoding='utf8'):
        ''' Create a text report.

        Arguments:
            report_path -- Path to report file
            mode        -- a for append, w (default) for create from scratch (overwrite existing file)
        '''
        if not path or path == TextReport.STDOUT:
            self.__path = TextReport.STDOUT
            self.__report_file = sys.stdout
            self.name = 'stdout'
            self.mode = None
            self.auto_flush = False
        elif path == TextReport.STRINGIO:
            self.__path = TextReport.STRINGIO
            self.__report_file = io.StringIO()
            self.name = 'StringIO'
            self.mode = None
            self.auto_flush = False
        else:
            self.__path = os.path.expanduser(path)
            self.__report_file = open(self.__path, mode, encoding=encoding)
            self.name = name if name else FileHelper.getfilename(self.__path)
            self.auto_flush = auto_flush
            self.mode = mode
        self.print = self.writeline  # just an alias

    @property
    def closed(self):
        return self.__report_file is None or self.__report_file.closed

    @property
    def file(self):
        return self.__report_file

    def content(self):
        ''' Return report content as a string if mode == STRINGIO else an empty string '''
        if isinstance(self.__report_file, io.StringIO):
            return self.__report_file.getvalue()
        else:
            return ''

    def write(self, *msg, separator=" ", level=0):
        out_string = separator.join(str(x) for x in msg)
        self.__report_file.write("\t" * level)
        self.__report_file.write(out_string)
        if self.auto_flush:
            self.__report_file.flush()

    def writeline(self, *msg, **kwargs):
        msg = msg + ('\n',)
        self.write(*msg, **kwargs)

    def header(self, *msg, **kwargs):
        header(*msg, print_out=self.writeline, **kwargs)

    def close(self):
        if self.mode and self.__report_file != sys.stdout:
            try:
                self.__report_file.flush()
                self.__report_file.close()
                self.__report_file = None
            except Exception as e:
                getLogger().exception("Error raised while saving report")
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def path(self):
        return self.__path

    @staticmethod
    def null():
        ''' Get a dev null report (print to nowhere)'''
        return TextReport('/dev/null')

    @staticmethod
    def string(**kwargs):
        return TextReport(TextReport.STRINGIO, **kwargs)


###############################################################################

class FileHub:
    ''' A helper class for working with multiple text reports at the same time
    '''
    def __init__(self, *filenames, working_dir='.', default_mode='a', ext='txt'):
        self.files = {}
        self.ext = ext if ext else ''
        self.working_dir = working_dir
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
    def replace_ext(file_path, ext):
        ''' Change extension of a file_path to something else (provide None to remove) '''
        if not file_path:
            raise Exception("File path cannot be empty")
        dirname = os.path.dirname(file_path)
        filename = FileHelper.getfilename(file_path)
        if ext:
            filename = filename + '.' + ext
        return os.path.join(dirname, filename)

    @staticmethod
    def replace_name(file_path, new_name):
        ''' Change the file name in a path but keep the extension '''
        if not file_path:
            raise Exception("File path cannot be empty")
        elif not new_name:
            raise Exception("New name cannot be empty")
        dirname = os.path.dirname(file_path)
        name, ext = os.path.splitext(os.path.basename(file_path))
        return os.path.join(dirname, new_name + ext)

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
    def read(a_file, mode='r', encoding='utf-8'):
        with open(a_file, mode=mode, encoding=encoding) as fileobj:
            return fileobj.read()


class AppConfig(object):

    ''' Application Configuration Helper
This class supports guessing configuration file location, and reads either INI (default) or JSON format.
    '''
    JSON = 'json'
    INI = 'ini'  # Python INI config file
    LOC_TEMPLATE = ['{wd}/.{n}', '{wd}/{n}', '{wd}/data/{n}', '{wd}/data/.{n}', '~/.{n}',
                    '~/.{n}/config', '~/.{n}/config.{mode}', '~/.config/{n}',
                    '~/.config/.{n}', '~/.config/{n}/config', '~/.config/{n}/config.{mode}',
                    '~/.config/{n}/{n}']

    def __init__(self, name, mode=INI, working_dir='.', extra_potentials=None):
        self.__name = name
        self.__mode = mode
        self.working_dir = working_dir
        self.__potential = []
        if extra_potentials:
            self.add_potential(*extra_potentials)
        self.add_potential(*AppConfig.LOC_TEMPLATE)
        self.__config = None
        self.__config_path = None

    def potentials(self):
        return self.__potential

    def _ptn2fn(self, pattern):
        ''' Pattern to filename '''
        return [pattern.format(wd=self.working_dir, n=self.__name, mode=self.__mode),
                pattern.format(wd=self.working_dir, n='{}.{}'.format(self.__name, self.__mode), mode=self.__mode)]

    def add_potential(self, *patterns):
        ''' Add a potential config file pattern '''
        for ptn in patterns:
            self.__potential.extend(self._ptn2fn(ptn))

    def locate_config(self):
        ''' Locate config file '''
        for f in self.__potential:
            f = FileHelper.abspath(f)
            if os.path.isfile(f):
                return f
        return None

    @property
    def config(self):
        ''' Read config automatically if required '''
        if self.__config is None:
            config_path = self.locate_config()
            if config_path:
                self.__config = self.read_file(config_path)
                self.__config_path = config_path
        return self.__config

    def read_file(self, file_path):
        ''' Read a configuration file and return configuration data '''
        getLogger().info("Loading app config from {} file: {}".format(self.__mode, file_path))
        if self.__mode == AppConfig.JSON:
            return json.loads(FileHelper.read(file_path), object_pairs_hook=OrderedDict)
        elif self.__mode == AppConfig.INI:
            config = configparser.ConfigParser(allow_no_value=True)
            config.read(file_path)
            return config

    def load(self, file_path):
        ''' Load configuration from a specific file '''
        self.clear()
        self.__config = self.read_file(file_path)

    def clear(self):
        self.__config = None
        return self
