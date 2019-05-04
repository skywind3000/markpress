#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# config.py - 
#
# Created by skywind on 2019/05/04
# Last Modified: 2019/05/04 23:07:13
#
#======================================================================
from __future__ import print_function, unicode_literals
import sys
import os
import ascmini


#----------------------------------------------------------------------
# config
#----------------------------------------------------------------------
ININAME = '~/.config/markpress/config.ini'
ININAME = os.path.abspath(os.path.expanduser(ININAME))
PRESENT = os.path.exists(ININAME)
MARKPRESS = os.environ.get('MARKPRESS', '').strip()

cfg = ascmini.ConfigReader(ININAME)
options = {}


#----------------------------------------------------------------------
# select
#----------------------------------------------------------------------
def select(section):
    if not PRESENT:
        raise FileNotFoundError("missing: " + ININAME)
    if section not in cfg.config:
        raise ValueError("config section missing: " + section)
    options['url'] = cfg.option(section, 'url', '').strip()
    options['user'] = cfg.option(section, 'user', '').strip()
    options['passwd'] = cfg.option(section, 'passwd', '').strip()
    options['tabsize'] = cfg.option(section, 'tabsize', 4)
    options['blog'] = cfg.option(section, 'blog', '').strip()
    options['engine'] = cfg.option(section, 'engine', '').strip()
    if not options['url']:
        raise ValueError('config error: empty url')
    if not options['user']:
        raise ValueError('config error: empty user')
    return True

try:
    select('default')
except:
    pass

if MARKPRESS:
    select(MARKPRESS)


#----------------------------------------------------------------------
# testing suit 
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        print(ININAME)
        print(options)
        return 0
    test1()



