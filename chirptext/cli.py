#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Command-line interface helper

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
import logging
import logging.config
import argparse
import json


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

class ChirpCLI(object):

    SETUP_COMPLETED = False


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Application logic
# -------------------------------------------------------------------------------

def setup_logging(filename, log_dir=None, force_setup=False):
    ''' Try to load logging configuration from a file. Set level to INFO if failed.
    '''
    if not force_setup and ChirpCLI.SETUP_COMPLETED:
        logging.debug("Master logging has been setup. This call will be ignored.")
        return
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if os.path.isfile(filename):
        with open(filename) as config_file:
            try:
                config = json.load(config_file)
                logging.config.dictConfig(config)
                logging.info("logging was setup using {}".format(filename))
                ChirpCLI.SETUP_COMPLETED = True
            except Exception as e:
                logging.exception("Could not load logging config")
                # default logging config
                logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)


def config_logging(args):
    ''' Override root logger's level '''
    if args.quiet:
        logging.getLogger().setLevel(logging.CRITICAL)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)


class CLIApp(object):
    ''' A simple template for command-line interface applications '''

    def __init__(self, desc, add_vq=True, add_tasks=True, **kwargs):
        """
        Init an app instance
        """
        self.__parser = argparse.ArgumentParser(description=desc, add_help=False)
        self.__parser.set_defaults(func=None)
        self.__add_vq = add_vq
        self.__config_logging = config_logging
        if 'config_logging' in kwargs:
            self.__config_logging = kwargs['config_logging']
        if add_vq:
            self.add_vq(self.__parser)
        if add_tasks:
            task_desc = kwargs['task_desc'] if 'task_desc' in kwargs else 'Task to be done'
            self.__tasks = self.__parser.add_subparsers(help=task_desc)
        else:
            self.__tasks = None
        self.__logger = None
        self.__name = kwargs['logger'] if 'logger' in kwargs else __name__

    def add_task(self, task, func=None, **kwargs):
        ''' Add a task parser '''
        if not self.__tasks:
            raise Exception("Tasks subparsers is disabled")
        if 'help' not in kwargs:
            if func.__doc__:
                kwargs['help'] = func.__doc__
        task_parser = self.__tasks.add_parser(task, **kwargs)
        if self.__add_vq:
            self.add_vq(task_parser)
        if func is not None:
            task_parser.set_defaults(func=func)
        return task_parser

    def add_vq(self, parser):
        ''' Add verbose & quiet options '''
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-v", "--verbose", action="store_true")
        group.add_argument("-q", "--quiet", action="store_true")

    @property
    def logger(self):
        ''' Lazy logger '''
        if self.__logger is None:
            self.__logger = logging.getLogger(self.__name)
        return self.__logger

    def run(self, func=None):
        ''' Run the app '''
        args = self.parser.parse_args()
        if self.__add_vq is not None and self.__config_logging:
            self.__config_logging(args)
        if args.func is not None:
            args.func(self, args)
        elif func is not None:
            func(self, args)
        else:
            self.parser.print_help()

    @property
    def parser(self):
        return self.__parser

    @property
    def tasks(self):
        return self.__tasks
