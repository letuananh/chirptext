#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import os
import codecs
import sys
import time
import itertools
import operator
if sys.version_info >= (3, 0):
	from itertools import zip_longest
else:
	from itertools import izip_longest

from collections import OrderedDict
# from chirptext.leutile import jilog, Timer, Counter, StringTool

JILOG_LOCATION = 'debug.txt'

def jilog(msg):
	try:
		sys.stderr.write(("%s\n" % str(msg)).encode("ascii","ignore").decode('ascii', 'ignore'))
		sys.stdout.write(("%s\n" % str(msg)).encode("ascii","ignore").decode('ascii', 'ignore'))
	except:
		# nah, dun care
		pass
	try:
		with codecs.open(JILOG_LOCATION, "a", encoding='utf-8') as logfile:
			# don't do this anymore
			# logfile.write("%s\n" % str(msg))
			pass
	except Exception as ex:
		# sys.stderr.write(str(ex))
		# nah, dun care
		pass

def uniquify(a_list):
	return list(OrderedDict(zip(a_list, range(len(a_list)))).keys())

def header(msg, level='h1'):
    if level == 'h1':
        print('-' * 80)
        print(msg)
        print('-' * 80)
    elif level == 'h2':
        print('\t%s' % msg)
        print('\t' + ('-' * 40))
    else:
        print('\t\t%s' % msg)
        print('\t\t' + ('-' * 20))


class Timer:
	''' Timer a task
	'''
	def __init__(self):
		self.start_time = time.time()
		self.end_time = time.time()
		
	def start(self, task_note=''):
		if task_note:
			jilog("[%s]\n" % (str(task_note),))
		self.start_time = time.time()
		return self
			
	def stop(self):
		self.end_time = time.time()
		return self
		
	def __str__(self):
		return "Execution time: %.2f sec(s)" % (self.end_time - self.start_time)
		
	def log(self, task_note = ''):
		jilog("%s - Note=[%s]\n" % (self, str(task_note)))
		return self
		
	def end(self, task_note=''):
			self.stop().log(task_note)

class Counter:
	def __init__(self, priority=None):
		self.count_map = {}
		self.priority = priority if priority else []
	
	def __getitem__(self, key):
		if key not in self.count_map:
			self.count_map[key] = 0
		return self.count_map[key]
	
	def __setitem__(self, key, value):
		self.count_map[key] = value
	
	def count(self, key):
		self[key] += 1

	def order(self, priority):
		self.priority = [ x for x in priority ]

	def get_report_order(self):
		order_list = []
		for x in self.priority:
			order_list.append([x, self[x]])
		for x in sorted(list(self.count_map.keys())):
			if x not in self.priority:
				order_list.append([x, self[x]])
		return order_list
		
	def summarise(self):
		for k, v in self.get_report_order():
			print( "%s: %d" % (k, v) )

	def save(self, file_loc):
		'''Save counter information to files'''
		with open(file_loc, 'w') as outfile:
			for k, v in self.get_report_order():
				outfile.write( "%s: %d\n" % (k, v) )

	def sorted_by_count(self):
		if sys.version_info >= (3, 0):
			return sorted(self.count_map.items(), key=operator.itemgetter(1), reverse=True)
		else:
			return sorted(self.count_map.iteritems(), key=operator.itemgetter(1), reverse=True)

class StringTool:
	@staticmethod
	def strip(a_str):
		return a_str.strip() if a_str else ''
	
	@staticmethod
	def to_str(a_str):
		return str(a_str) if a_str else ''

class FileHub:
	def __init__(self, ext='.log'):
		self.files = {}
		self.ext = ext if ext else ''
	
	def __getitem__(self, key):
		if not self.files.has_key(key):
			self.addtext(key)
		return self.files[key]
	
	def __setitem__(self, key, value):
		self.files[key] = value
		
	def addtext(self, key):
		self.files[key] = open(key + self.ext, 'a')
		
	def create(self, key):
		self.files[key] = open(key + self.ext, 'w')
		
	def writeline(self, key, text):
		self[key].write('%s\n' % (text,))
		self[key].flush()
	
	def flush(self):
		for key in self.files.keys():
			self[key].flush()
			
	def close(self):
		for key in self.files.keys():
			self[key].flush()
			self[key].close()

class FileTool:
	@staticmethod
	def getfilename(file_path):
		''' Get filename without extension
		'''
		return os.path.splitext(getfullfilename(file_path))[0]

	@staticmethod
	def getfullfilename(file_path):
		''' Get full filename (with extension)
		'''
		if file_path:
			return os.path.basename(file_path)
		else:
			return ''

def main():
	print("This is an utility module, not an application.")
	pass

if __name__ == "__main__":
	main()

if sys.version_info >= (3, 0):
	def grouper(iterable, n, fillvalue=None):
		args = [iter(iterable)] * n
		return zip_longest(fillvalue=fillvalue, *args)
else:
	def grouper(iterable, n, fillvalue=None):
		args = [iter(iterable)] * n
		return izip_longest(fillvalue=fillvalue, *args)


