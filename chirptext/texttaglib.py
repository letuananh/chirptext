#!/usr/bin/env python3
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

from collections import namedtuple

OPEN_TAG = "<wnsk>"
CLOSE_TAG = "</wnsk>"

TokenInfo = namedtuple("TokenInfo", ['text', 'sk'])


class TagInfo(object):

    GOLD = 'gold'
    ISF = 'isf'
    DEFAULT = 'n/a'

    def __init__(self, cfrom, cto, label, source=DEFAULT):
        self.cfrom = cfrom
        self.cto = cto
        self.label = label
        self.source = source


class TaggedSentence:

    def __init__(self, text, tags):
        self.text = text
        self.tags = tags

    def __str__(self):
        return format_tag(self)


class StringBuffer:
    def __init__(self, text=None):
        self.buff = []
        self.__length = 0
        self.append(text)
        self.write = self.append

    def clear(self):
        del self.buff[:]

    def append(self, text):
        if text:
            self.buff.append(text)
            self.__length += len(text)
        return self

    def writeline(self, text):
        return self.append(text).newline()

    def newline(self):
        return self.append('\n')

    def size(self):
        return self.__length

    def __len__(self):
        return self.__length

    def __str__(self):
        return ''.join(self.buff)

# TODO: This is a crazy mess, should be cleaned ASAP


def tag_to_token(tag):
    tag_text = tag[len(OPEN_TAG): -len(CLOSE_TAG)]
    parts = tag_text.split('|')
    if parts and len(parts) == 2:
        text = parts[0]
        sk = parts[1]
        return TokenInfo(text, sk)
    else:
        return None


def find_tags(sent):
    buff=StringBuffer()
    cur=0
    tags = []

    while cur < len(sent):
        #print("cur=%s - sent=%s" % (cur,len(sent)))
        cfrom=sent.find(OPEN_TAG, cur)
        cto=sent.find(CLOSE_TAG, cur)
        if cfrom >= 0:
            tag=sent[cfrom:cto+len(CLOSE_TAG)]
            if cfrom > cur:
                buff.append(sent[cur:cfrom])
            token = tag_to_token(tag)
            tags.append(TagInfo(buff.size(), buff.size()+len(token.text), token.sk))
            buff.append(token.text)
            cur = cto+len(CLOSE_TAG)
        else:
            buff.append(sent[cur:len(sent)+1])
            cur = len(sent)
    return TaggedSentence(str(buff), tags)


def draw_vertical_line(buff, all_cfrom, start_from=0):
    cur = start_from
    for cfrom in all_cfrom:
        if start_from > cfrom:
            continue
        if cfrom > cur:
            buff.write(' ' * (cfrom - cur))
            cur += cfrom - cur
        if cfrom == cur:
            buff.write('|')
        cur = cfrom+1
    buff.newline()  # new line


def format_tag(tagged_sentence, show_from_to=False):
    buff = StringBuffer()
    buff.writeline(tagged_sentence.text)
    cur = 0
    # print alignment line
    for tag in tagged_sentence.tags:
        if tag.cfrom > cur:
            buff.write(' ' * (tag.cfrom - cur))
            cur += tag.cfrom - cur
        if tag.cfrom == cur:
            buff.write('=' * (tag.cto - tag.cfrom))
        cur = tag.cto
    buff.newline()
    # print vertical lines
    all_cfrom = sorted([x.cfrom for x in tagged_sentence.tags])
    for tag in tagged_sentence.tags:
        tag_label = '[ %s ]' % tag.label if not show_from_to else '[ %s (%s:%s) ]' % (tag.label, tag.cfrom, tag.cto)
        draw_vertical_line(buff, [ x for x in all_cfrom if x >= tag.cfrom ], 0)
        buff.write(' ' * tag.cfrom + tag_label)
        draw_vertical_line(buff, all_cfrom, tag.cfrom+len(tag_label))
    return str(buff)


def replace_tag(sent, tag, something_else):
    if not tag or tag.cfrom > tag.cto or tag.cfrom < 0:
        return None 
    return sent[0:tag.cfrom] + something_else + sent[tag.cto:len(sent)+1]


def tag_sent(sent):
    taginfo = find_tags(sent)
    print('-' * 80)
    # Nice formatting
    print(format_tag(taginfo))


def writelines(lines, filepath, verbose=True):
    if verbose:
        print("Writing to: %s" % (filepath,))
    with open(filepath, 'w') as afile:
        for line in lines:
            afile.write(line)
            afile.write('\n')


def main():
    print("This is a library, not an application.")
    pass

if __name__ == "__main__":
    main()
