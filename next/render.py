#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# render.py - 
#
# Created by skywind on 2019/05/06
# Last Modified: 2019/05/06 23:10:23
#
#======================================================================
from __future__ import print_function, unicode_literals
import sys
import os
import bs4
import ascmini
import config


#----------------------------------------------------------------------
# 2/3 compatible
#----------------------------------------------------------------------
if sys.version_info[0] >= 3:
    unicode = str


#----------------------------------------------------------------------
# INTERNAL
#----------------------------------------------------------------------
ENGINES = ['dot', 'circo', 'neato', 'osage', 'twopi']
VIZPATH = ['.']


#----------------------------------------------------------------------
# GraphViz
#----------------------------------------------------------------------
def graphviz(engine, text):
    if engine not in ENGINES:
        raise ValueError('Invalid Engine: %s'%engine)
    path = [ n for n in VIZPATH ]
    if config.options['graphviz']:
        viz = config.options['graphviz']
        if os.path.isdir(viz):
            path.append(viz)
    exe = ascmini.posix.search_cmd(engine, path)
    if not exe:
        raise FileNotFoundError('Missing GraphViz executable: ' + engine)
    args = [exe, '-Tsvg']
    code, stdout, stderr = ascmini.call(args, text)
    if stdout:
        stdout = stdout.decode('utf-8', 'ignore')
    if stderr:
        stderr = stderr.decode('utf-8', 'ignore')
    if code != 0:
        raise ChildProcessError('error: %s: %s'%(engine, stderr))
    return stdout


#----------------------------------------------------------------------
# render html
#----------------------------------------------------------------------
class HtmlRender (object):
    
    def __init__ (self, html):
        self._origin_html = html
        self._soup = bs4.BeautifulSoup(html, 'html.parser')

    def process_viz (self):
        soup = self._soup
        for pre in soup.find_all('pre'):
            code = pre.code
            if code is None:
                continue
            if 'class' not in code.attrs:
                continue
            if not code['class']:
                continue
            engine = None
            for cls in code['class']:
                if cls.startswith('viz-'): 
                    name = cls[4:]
                    if name in ENGINES:
                        engine = name
                        break
            if engine is None:
                continue
            tag = self._viz_replace(engine, code.text)
            pre.insert_before(tag)
            pre.decompose()
        return 0

    def _viz_replace (self, engine, text):
        try:
            output = graphviz(engine, text)
            soup = bs4.BeautifulSoup(output, 'html.parser')
            # soup = bs4.BeautifulSoup(output, 'lxml')
            svg = soup.svg.extract()
            p = self._soup.new_tag('pre')
            p.insert(0, svg)
            # print(svg)
        except:
            text = ascmini.callstack()
            pre = self._soup.new_tag('pre')
            code = self._soup.new_tag('code')
            pre.insert(0, code)
            code.string = text
            return pre
        return p

    def render (self):
        return self._soup.prettify()



#----------------------------------------------------------------------
# testing suit
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        import utils
        VIZPATH.append('d:/dev/tools/graphviz/bin')
        doc = utils.MarkdownDoc('../content/test2.md')
        html = doc.convert('')
        hr = HtmlRender(html)
        hr.process_viz()
        print(hr.render())
        # print(unicode(soup))
        return 0
    def test2():
        print(ascmini.posix.search_cmd('gcc', ['d:/dev/tools/graphviz/bin']))
        VIZPATH.append('d:/dev/tools/graphviz/bin')
        text = 'digraph G {\n A -> B\nB -> C\nB -> D\n}'
        output = graphviz('dot', text)
        print(output)
        return 0
    test1()



