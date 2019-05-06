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
import wordpress


#----------------------------------------------------------------------
# load markdown
#----------------------------------------------------------------------
def markpress_load(filename):
    if not os.path.exists(filename):
        config.fatal('file not find: ' + filename)
    doc = utils.MarkdownDoc(filename)
    return doc


#----------------------------------------------------------------------
# convert
#----------------------------------------------------------------------
def markpress_convert(doc):
    doc._html = doc.convert('config')
    return doc._html


#----------------------------------------------------------------------
# update file
#----------------------------------------------------------------------
def markpress_update(filename):
    doc = markpress_load(filename)
    if not doc._uuid:
        config.perror(filename, 1, 'uuid not find in the markdown meta-header')
        return -1
    uuid = doc._uuid.strip()
    if not uuid.isdigit():
        config.perror(filename, 1, 'invalid uuid %s'%uuid)
        return -2
    post = {}
    post['id'] = uuid
    post['title'] = doc._title
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
    return 0


#----------------------------------------------------------------------
# 
#----------------------------------------------------------------------
def markpress_preview(filename):
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
            print('usage: markpress {-n --new} <filename>')
            print('Create a new post and save it to file. Dump to stdout')
            print('if filename is a hyphen (-).')
        elif 'p' in options or 'preview' in options:
            print('usage: markpress {-p --preview} <filename>')
            print('Preview markdown')
        elif 'u' in options or 'update' in options:
            print('usage: markpress {-u --update} <filename>')
            print('Update file to wordpress server')
        else:
            config.fatal('what help do you need ?')
    elif 'n' in options or 'new' in options:
        if not args:
            config.fatal('missing file name')
        name = args[0]
        if name == '-':
            fp = sys.stdout
        elif os.path.exists(name):
            config.fatal('file already exists: ' + name)
        wp = config.wp_client()
        pid = wp.post_new() 
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
        fp.write('---\n')
    elif 'u' in options or 'update' in options:
        if not args:
            config.fatal('missing file name')
        markpress_update(args[0])
    elif 'p' in options or 'preview' in options:
        if not args:
            config.fatal('missing file name')
        markpress_preview(args[0])
    else:
        print('usage: markpress <operation> [...]')
        print('operations:')
        print('    markpress {-n --new} <filename>')
        print('    markpress {-u --update} <filename>')
        print('    markpress {-p --preview} <filename>')
        print()
        print("use 'markpress {-h --help}' with an operation for detail")
    return 0


#----------------------------------------------------------------------
# testing suit 
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        return 0
    def test9():
        args = ['', '-n', '-']
        args = []
        args = ['', '-h', '-n']
        main(args)
        return 0
    test9()
    # main()



