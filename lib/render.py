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
VIZPATH = []

SCRIPT_ENABLE = True
SCRIPT_ENCODING = None
SCRIPT_PATH = []


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
# External
#----------------------------------------------------------------------
def script_eval(script, text, binary = False):
    path = [ n for n in SCRIPT_PATH ]
    if config.options['path']:
        cmd = config.options['path']
        if os.path.isdir(cmd):
            path.append(cmd)
    exe = ascmini.posix.search_cmd(script, path)
    if not exe:
        raise FileNotFoundError('Missing executable: ' + script)
    encoding = config.options['encoding']
    if not encoding:
        encoding = SCRIPT_ENCODING
    if not encoding:
        try:
            import locale
            encoding = locale.getdefaultlocale()[1]
        except:
            encoding = sys.getdefaultencoding()
    if not isinstance(text, bytes):
        text = text.encode(encoding, 'ignore')
    code, stdout, stderr = ascmini.call([exe], text)
    if not binary:
        if stdout:
            stdout = stdout.decode(encoding, 'ignore')
        if stderr:
            stderr = stderr.decode(encoding, 'ignore')
    if code != 0:
        raise ChildProcessError('error: %s: %s'%(script, stderr))
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
                elif cls.startswith('cmd-') and SCRIPT_ENABLE:
                    name = str(cls).strip()
                    mode, _, _ = name[4:].partition('-')
                    if mode.strip() in ('text', 'html', 'png', 'jpeg'):
                        engine = name
                        break
            if engine is None:
                continue
            if engine.startswith('cmd-'):
                tag = self._cmd_replace(engine, code.text)
            else:
                tag = self._viz_replace(engine, code.text)
            pre.insert_before(tag)
            pre.decompose()
        return 0

    def _cmd_replace (self, engine, text):
        mode, _, script = engine[4:].strip().partition('-')
        mode = mode.strip()
        binary = (mode in ('png', 'jpeg'))
        try:
            output = script_eval(script.strip(), text, binary)
            if mode == 'text':
                p = self._soup.new_tag('pre')
                code = self._soup.new_tag('code')
                p.insert(0, code)
                code.string = output
            elif mode == 'html':
                soup = bs4.BeautifulSoup(output, 'html.parser')
                p = self._soup.new_tag('p')
                p.insert(0, soup)
            else:
                import base64
                html = '<img src="data:image/%s;base64,\n'%mode
                if sys.version_info[0] >= 3:
                    xrange = range
                s = base64.b64encode(output)
                if isinstance(s, bytes):
                    s = s.decode('utf-8', 'ignore')
                t = [ s[pos:pos + 76] for pos in xrange(0, len(s), 76) ]
                t = '\n'.join(t)
                html = html + t + '"  alt="%s" />\n'%script
                soup = bs4.BeautifulSoup(html, 'html.parser')
                p = self._soup.new_tag('p')
                p.insert(0, soup)
        except:
            text = ascmini.callstack()
            pre = self._soup.new_tag('pre')
            code = self._soup.new_tag('code')
            pre.insert(0, code)
            code.string = text
            return pre
        return p

    def _viz_replace (self, engine, text):
        try:
            output = graphviz(engine, text)
            soup = bs4.BeautifulSoup(output, 'html.parser')
            # soup = bs4.BeautifulSoup(output, 'lxml')
            svg = soup.svg.extract()
            p = self._soup.new_tag('pre')
            p.insert(0, svg)
            p['style'] = 'background:none; border:0px;'
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
        # return self._soup.prettify()
        return unicode(self._soup)



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
    def test3():
        t = script_eval('d:/filter2', 'test', False)
        print('-----')
        print(t)
        return 0
    def test4():
        import utils
        SCRIPT_PATH.append('e:/site/markpress/test/filters')
        global SCRIPT_ENCODING
        # SCRIPT_ENCODING = 'utf-8'
        doc = utils.MarkdownDoc('../test/1.md')
        html = doc.convert('markdown')
        # html = doc.convert('')
        hr = HtmlRender(html)
        hr.process_viz()
        print(hr.render())
        return 0
    test4()



