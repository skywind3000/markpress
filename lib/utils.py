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
import utime


#----------------------------------------------------------------------
# extras
#----------------------------------------------------------------------
MD_EXTRAS = ['metadata', 'fenced-code-blocks', 'cuddled-list', 
    'tables', 'footnotes', 'highlightjs-lang', 'target-blank-links',
    'use-file-vars', 'code-friendly']

PANDOC_FLAGS = ['--no-highlight']

PANDOC_EXTENSION = ['fancy_lists', 'fenced_code_blocks', 
    'fenced_code_attributes']

PYMD_EXTENSION = [ 'fenced_code', 'footnotes', 'tables', 'meta' ]


#----------------------------------------------------------------------
# Error
#----------------------------------------------------------------------
class ConvertError (ValueError):
    pass


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
        self._error = None
        self._status = None
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
                else:
                    break
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
        self._slug = self._meta.get('slug', None)
        self._date = self._meta.get('date', None)
        self._status = self._meta.get('status', 'draft')
        if not self._uuid:
            self._uuid = None
        if not self._title:
            self._title = None
        if not self._cats:
            self._cats = None
        if not self._tags:
            self._tags = None
        return True

    def _fenced_code_block (self, content):
        output = []
        source = []
        state = 0
        mark = ''
        lang = None
        for line in content.split('\n'):
            line = line.rstrip('\r\n\t ')
            if state == 0:
                if not line.startswith('```'):
                    output.append(line)
                    continue
                test = line.lstrip('`')
                size = len(line) - len(test)
                mark = '`' * size
                lang = test.strip()
                state = 1
                source = []
            elif state == 1:
                if line != mark:
                    source.append(line)
                    continue
                src = '\n'.join(source).strip('\n')
                head = '<pre><code>'
                if lang:
                    head = '<pre><code class="%s">'%lang
                replacements = [
                    ("&amp;", "&"),
                    ("&lt;", "<"),
                    ("&gt;", ">")
                ]
                for new, old in replacements:
                    src = src.replace(old, new)
                output.append(head + src)
                output.append('</code></pre>')
                state = 0
        return '\n'.join(output)

    def _convert_default (self, content):
        import markdown2
        content = self._fenced_code_block(content)
        tabsize = config.options['tabsize']
        extras = [ n for n in MD_EXTRAS ]
        if config.options['extras']:
            for n in config.options['extras'].split(','):
                extras.append(n.strip())
        md = markdown2.Markdown(extras = extras, tab_width = tabsize)
        html = md.convert(content)
        if sys.version_info[0] >= 3:
            unicode = str
        text = unicode(html)
        return text

    def _convert_pandoc (self, content):
        input = content.encode('utf-8', 'ignore')
        args = ['pandoc', '-f', 'markdown', '-t', 'html']
        args.extend(PANDOC_FLAGS)
        for exts in PANDOC_EXTENSION:
            if exts[:1] not in ('+', '-'):
                exts = '+' + exts
            args[2] += exts
        code, stdout, stderr = ascmini.call(args, input)
        self._error = None
        if code != 0:
            stderr = stderr.decode('utf-8', 'ignore')
            error = ConvertError("pandoc exits with code %d: %s" % (
                code, stderr))
            error.stdout = stderr
            raise error
        return stdout.decode('utf-8', 'ignore')

    # require: https://github.com/Python-Markdown/markdown/
    def _convert_markdown (self, content):
        import markdown
        exts = [ n for n in PYMD_EXTENSION ]
        if config.options['extensions']:
            for n in config.options['extensions'].split(','):
                exts.append(n.strip())
        path = os.path.expanduser('~/.config/markpress')
        name = os.path.join(path, 'extensions.py')
        sys.path.insert(0, path)
        argv = {}
        argv['extensions'] = exts
        if os.path.exists(name):
            import extensions
            if 'extensions' in extensions.__dict__:
                exts.extend(extensions.extensions)
            if 'extension_configs' in extensions.__dict__:
                argv['extension_configs'] = extensions.extension_configs
        html = markdown.markdown(content, **argv)
        return html

    # engine: native, markdown, pandoc, auto, config
    def convert (self, engine):
        if engine is None:
            engine = ''
        engine = engine.strip().lower()
        if engine in ('markdown2', 'default', '0', '', 'native', 0):
            engine = ''
        if engine == 'config':
            engine = config.options['engine']
        if engine == 'auto':
            try:
                import markdown
                engine = 'markdown'
            except ImportError:
                engine = 'default'
        content = self._content
        if engine == 'markdown':
            return self._convert_markdown(content)
        elif engine == 'pandoc':
            return self._convert_pandoc(content)
        return self._convert_default(content)

    def link (self):
        url = config.options['url']
        if not url.endswith('/'):
            url += '/'
        return url + '?' + self._uuid


#----------------------------------------------------------------------
# utc datetime 
#----------------------------------------------------------------------
def utc_datetime(text):
    import datetime
    ts = utime.read_timestamp(text)
    return datetime.datetime.utcfromtimestamp(ts)


#----------------------------------------------------------------------
# testing suit 
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        doc = MarkdownDoc('../content/test.md')
        print(doc._meta)
        print(doc._cats)
        print(doc._tags)
        print(doc.convert(''))
        return 0
    def test2():
        text = ascmini.execute(['cmd', '/c', 'dir'], capture = True)
        print('---')
        print(text.decode('gbk'))
        return 0
    def test3():
        import markdown2
        extras = MD_EXTRAS
        html = markdown2.markdown('\n`````text\n```cpp\ntext\n```\n`````\n', extras = extras)
        print(html)
        return 0
    def test4():
        doc = MarkdownDoc('../content/2.md')
        html = doc.convert('markdown')
        print(html)
        return 0
    test4()


