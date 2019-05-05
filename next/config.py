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
# fatal 
#----------------------------------------------------------------------
def fatal(message, code = 1):
    message = message.rstrip('\n')
    sys.stderr.write('Fatal: ' + message + '\n')
    sys.stderr.flush()
    sys.exit(code)
    return 0


#----------------------------------------------------------------------
# use proxy
#----------------------------------------------------------------------
def proxy(url):
    url = url.strip()
    import socket
    if '_socket_' not in socket.__dict__:
        socket._socket_ = socket.socket
    if not url:
        socket.socket = socket._socket_
        return True
    try:
        import socks
    except ImportError:
        fatal('PySocks module is required')
        return False
    if url.startswith('socks5://'):
        body = url[9:]
        mode = socks.SOCKS5
    elif url.startswith('socks4://'):
        body = url[9:]
        mode = socks.SOCKS4
    elif url.startswith('http://'):
        body = url[7:]
        mode = socks.HTTP
    return 0


#----------------------------------------------------------------------
# testing suit 
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        print(ININAME)
        print(options)
        return 0
    def test2():
        fatal("fuck you")
        return 0
    test2()



