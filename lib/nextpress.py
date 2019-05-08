#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# nextpress.py - 
#
# Created by skywind on 2019/05/05
# Last Modified: 2019/05/05 16:50:15
#
#======================================================================
from __future__ import print_function, unicode_literals
import sys
import os
import time
import config
import ascmini
import utils


#----------------------------------------------------------------------
# markdown render 
#----------------------------------------------------------------------
def markpress_render(doc):
    html = doc.convert('config')
    try:
        import render
    except ImportError:
        return html
    hr = render.HtmlRender(html)
    hr.process_viz()
    return hr.render()


#----------------------------------------------------------------------
# load markdown
#----------------------------------------------------------------------
def markpress_load(filename):
    if not os.path.exists(filename):
        config.fatal('file not find: ' + filename)
    doc = utils.MarkdownDoc(filename)
    if not doc._uuid:
        config.perror(filename, 1, 'uuid not find in the markdown meta-header')
        return None
    uuid = doc._uuid.strip()
    if not uuid.isdigit():
        config.perror(filename, 1, 'invalid uuid %s'%uuid)
        return None
    return doc


#----------------------------------------------------------------------
# page maker
#----------------------------------------------------------------------
def markpress_page_make(html, title):
    output = ''
    output += '<html>\n<head>\n'
    output += '<meta charset="UTF-8" />\n'
    if title:
        text = ascmini.web.text2html(title)
        output += '<title>%s</title>\n'%text
    css = config.template['style.css']
    if css:
        output += '<style type="text/css">\n'
        output += css
        output += '\n</style>\n'
    header = config.template['header.html']
    if header:
        output += header
        output += '\n'
    output += '</head>\n\n<body>\n\n'
    output += '<!--markdown start-->\n'
    output += html
    output += '\n\n'
    output += '<!--markdown endup-->\n\n'
    footer = config.template['footer.html']
    if footer:
        output += footer
        output += '\n'
    output += '</body>\n\n</html>\n\n'
    return output


#----------------------------------------------------------------------
# update file
#----------------------------------------------------------------------
def markpress_update(filename):
    doc = markpress_load(filename)
    if not doc:
        return -1
    uuid = doc._uuid
    post = {}
    post['id'] = uuid
    post['title'] = doc._title
    post['content'] = markpress_render(doc)
    status = doc._status
    if status not in ('', 'draft', 'private', 'publish'):
        config.perror(filename, 1, 'invalid status %s'%status)
        return -3
    post['status'] = status and status or 'draft'
    if doc._cats:
        post['category'] = doc._cats
    if doc._tags:
        post['tag'] = doc._tags
    if doc._slug:
        post['slug'] = doc._slug
    wp = config.wp_client()
    wp.post_edit(post)
    pp = wp.post_get(uuid)
    print('post uuid=%s updated: %s'%(uuid, filename))
    print('%s'%pp.link) 
    return 0


#----------------------------------------------------------------------
# fetch info
#----------------------------------------------------------------------
def markpress_info(filename):
    doc = markpress_load(filename)
    if not doc:
        return -1
    uuid = doc._uuid
    wp = config.wp_client()
    pp = wp.post_get(uuid)
    print('uuid: %s'%uuid)
    print('title: %s'%doc._title)
    print('link: %s'%pp.link)
    return 0


#----------------------------------------------------------------------
# convert
#----------------------------------------------------------------------
def markpress_compile(filename, outname):
    doc = markpress_load(filename)
    if not doc:
        return -1
    doc._html = markpress_render(doc)
    content = markpress_page_make(doc._html, doc._title)
    if (not outname) or (outname == '-'):
        fp = sys.stdout
    else:
        import codecs
        fp = codecs.open(outname, 'w', encoding = 'utf-8')
    fp.write(content)
    if fp != sys.stdout:
        fp.close()
    return 0


#----------------------------------------------------------------------
# open in browser
#----------------------------------------------------------------------
def markpress_open(filename, preview):
    doc = markpress_load(filename)
    if not doc:
        return -1
    url = doc.link()
    if preview:
        url = url + '&preview=true'
    import subprocess
    subprocess.call(['cmd.exe', '/C', 'start', url])
    return 0


#----------------------------------------------------------------------
# 
#----------------------------------------------------------------------
def markpress_preview(filename):
    markpress_open(filename, True)
    return 0


#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------
def main(argv = None):
    if argv is None:
        argv = sys.argv
    options, args = ascmini.utils.getopt(argv[1:])
    if not config.PRESENT:
        config.fatal('missing config: ' + config.ININAME)
    if 'site' in options:
        site = options['site'].strip()
        if site:
            if site not in config.cfg.config:
                config.fatal('config section mission: ' + site)
            try:
                config.select(site)
            except ValueError as e:
                config.fatal(str(e))
    if config.options['proxy']:
        config.proxy(config.options['proxy'])
    if 'h' in options or 'help' in options:
        if 'n' in options or 'new' in options:
            print('usage: markpress {-n --new} [--site=SITE] <filename>')
            print('Create a new post and save it to file. Dump to stdout')
            print('if filename is a hyphen (-).')
        elif 'u' in options or 'update' in options:
            print('usage: markpress {-u --update} [--site=SITE] <filename>')
            print('Update file to wordpress server')
        elif 'i' in options or 'info' in options:
            print('usage: markpress {-i --info} [--site=SITE] <filename>')
            print('Get post info')
        elif 'c' in options or 'compile' in options:
            print('usage: markpress {-c --compile} [--site=SITE] <filename> [outname]')
            print('Compile markdown to html')
        elif 'o' in options or 'open' in options:
            print('usage: markpress {-o --open} <filename>')
            print('Open post in browser')
        elif 'p' in options or 'preview' in options:
            print('usage: markpress {-p --preview} [--site=SITE] <filename>')
            print('Preview markdown')
        else:
            config.fatal('what help do you need ?')
    elif 'n' in options or 'new' in options:
        if not args:
            config.fatal('missing file name')
        name = args[0]
        if name == '-':
            fp = sys.stdout
        elif os.path.exists(name):
            if 'f' not in options:
                config.fatal('file already exists: ' + name)
        wp = config.wp_client()
        pid = wp.post_new()
        pp = wp.post_get(pid)
        if name != '-':
            import codecs
            fp = codecs.open(name, 'w', encoding = 'utf-8')
        fp.write('---\n')
        fp.write('uuid: ' + str(pid) + '\n')
        fp.write('title: \n')
        fp.write('status: draft\n')
        fp.write('categories: \n')
        fp.write('tags: \n')
        fp.write('slug: \n')
        fp.write('---\n\n')
        if name != '-':
            print('new post uuid=%s saved in %s'%(pid, name))
            print(pp.link)
    elif 'u' in options or 'update' in options:
        if not args:
            config.fatal('missing file name')
        markpress_update(args[0])
    elif 'i' in options or 'info' in options:
        if not args:
            config.fatal('missing file name')
        markpress_info(args[0])
    elif 'c' in options or 'compile' in options:
        if not args:
            config.fatal('missing file name')
        if len(args) >= 2:
            outname = args[1]
        else:
            outname = os.path.splitext(args[0])[0] + '.html'
        markpress_compile(args[0], outname)
    elif 'o' in options or 'open' in options:
        if not args:
            config.fatal('missing file name')
        markpress_open(args[0], False)
    elif 'p' in options or 'preview' in options:
        if not args:
            config.fatal('missing file name')
        markpress_preview(args[0])
    else:
        print('usage: markpress <operation> [...]')
        print('operations:')
        print('    markpress {-n --new} <filename>')
        print('    markpress {-u --update} <filename>')
        print('    markpress {-i --info} <filename>')
        print('    markpress {-c --compile} <filename> [outname]')
        print('    markpress {-o --open} <filename>')
        print('    markpress {-p --preview} <filename>')
        print()
        print("use 'markpress {-h --help}' with an operation for detail")
    return 0


#----------------------------------------------------------------------
# testing suit 
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        args = ['', '-n', '-f', '../content/1.md']
        args = ['', '-u', '../content/1.md']
        main(args)
        return 0
    def test2():
        args = ['', '-i', '../content/1.md']
        args = ['', '-c', '../content/1.md']
        # args = ['', '-c', '../content/1.md', '-']
        main(args)
        return 0
    def test9():
        args = ['', '-n', '-']
        args = []
        args = ['', '-h', '-n']
        main(args)
        return 0
    test1()
    # main()



