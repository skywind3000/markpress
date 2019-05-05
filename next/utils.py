#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# utils.py - 
#
# Created by skywind on 2019/05/04
# Last Modified: 2019/05/04 22:58:10
#
#======================================================================
from __future__ import print_function, unicode_literals
import sys
import os
import time
import config
import ascmini


#----------------------------------------------------------------------
# extras
#----------------------------------------------------------------------
MD_EXTRAS = ['metadata', 'fenced-code-blocks', 'cuddled-list', 
    'tables', 'footnotes', 'highlightjs-lang']


#----------------------------------------------------------------------
# MarkdownDoc 
#----------------------------------------------------------------------
class MarkdownDoc (object):

    def __init__ (self, filename):
        self._filename = os.path.abspath(filename)
        self._content = ascmini.posix.load_file_text(filename)
        self._html = None
        self._meta = {}
        self._cats = []
        self._tags = []
        self._uuid = None
        self._title = None
        self.__parse()

    def __parse_list (self, text):
        if not text:
            text = ''
        if isinstance(text, bytes):
            text = text.decode('utf-8', 'ignore')
        if '\uff0c' in text:
            text = text.replace('\uff0c', ',')
        parts = []
        for part in text.split(','):
            part = part.strip()
            if part:
                parts.append(part)
        return parts

    def __parse_meta (self, content):
        state = 0
        meta = {}
        size = len(content)
        pos = 0
        while pos < size:
            end = content.find('\n', pos)
            if end < 0:
                end = size
            line = content[pos:end]
            pos = end + 1
            line = line.rstrip('\r\n\t ')
            if not line:
                continue
            if state == 0:
                if line == ('-' * len(line)) and len(line) >= 3:
                    state = 1
            elif state == 1:
                if line == ('-' * len(line)) and len(line) >= 3:
                    state = 2
                elif ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip()
                    if key:
                        meta[key] = value.strip()
            else:
                break
        return meta

    def __parse (self):
        self._meta = self.__parse_meta(self._content)
        self._uuid = self._meta.get('uuid', None)
        self._title = self._meta.get('title', None)
        self._cats = self.__parse_list(self._meta.get('categories'))
        self._tags = self.__parse_list(self._meta.get('tags'))
        if not self._uuid:
            self._uuid = None
        if not self._title:
            self._title = None
        if not self._cats:
            self._cats = None
        if not self._tags:
            self._tags = None
        return True

    def _convert_markdown2 (self, content):
        import markdown2
        md = markdown2.Markdown(extras = MD_EXTRAS)
        html = md.convert(content)
        return html

    def convert (self):
        return self._convert_markdown2(self._content)



#----------------------------------------------------------------------
# testing suit 
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        doc = MarkdownDoc('../content/test.md')
        print(doc._meta)
        print(doc._cats)
        print(doc._tags)
        print(doc.convert())
        return 0
    test1()


