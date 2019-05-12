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
# loading
#----------------------------------------------------------------------
ININAME = '~/.config/markpress/config.ini'
ININAME = os.path.abspath(os.path.expanduser(ININAME))
PRESENT = os.path.exists(ININAME)
MARKPRESS = os.environ.get('MARKPRESS', '').strip()

cfg = ascmini.ConfigReader(ININAME)
options = {}


#----------------------------------------------------------------------
# default config
#----------------------------------------------------------------------
options['engine'] = cfg.option('default', 'engine', '').strip()
options['tabsize'] = cfg.option('default', 'tabsize', 4)
options['graphviz'] = cfg.option('default', 'graphviz', '').strip()
options['extensions'] = cfg.option('default', 'extensions', '').strip()
options['extras'] = cfg.option('default', 'extras', '').strip()
options['proxy'] = None


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
    options['blog'] = cfg.option(section, 'blog', '').strip()
    options['proxy'] = cfg.option(section, 'proxy', '').strip()
    if not options['url']:
        raise ValueError('config error: empty url')
    if not options['user']:
        raise ValueError('config error: empty user')
    return True

try:
    select('0')
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
# output error
#----------------------------------------------------------------------
def perror(fname, line, text):
    sys.stderr.write('%s:%d: error: %s\n'%(fname, line, text))
    sys.stderr.flush()
    return 0


#----------------------------------------------------------------------
# template
#----------------------------------------------------------------------
template = {}

def _load_template():
    names = ['style.css', 'header.html', 'footer.html']
    home = os.path.expanduser('~/.config/markpress')
    for name in names:
        fn = os.path.join(home, name)
        text = ascmini.posix.load_file_text(fn)
        if text:
            text = '\n'.join([ t.rstrip('\r\n') for t in text.split('\n') ])
        template[name] = text
        # print('name', len(template[name] and template[name] or ''))
    return True

_load_template()


#----------------------------------------------------------------------
# use proxy
#----------------------------------------------------------------------
def proxy(url):
    url = url.strip()
    import socket
    if '_socket_' not in socket.__dict__:
        socket._socket_ = socket.socket
    if (not url) or (url in ('raw', 'tcp', '', 'native')):
        socket.socket = socket._socket_
        return True
    try:
        import socks
    except ImportError:
        fatal('PySocks module is required')
        return False
    res = ascmini.web.url_parse(url)
    protocol = socks.HTTP
    if res.scheme == 'socks4':
        protocol = socks.SOCKS4
    elif res.scheme in ('socks5', 'socks'):
        protocol = socks.SOCKS5
    port = res.port
    if not port:
        port = (protocol == socks.HTTP) and 80 or 1080
    args = [protocol, res.hostname, port, True, res.username, res.password]
    socks.set_default_proxy(*args)
    socket.socket = socks.socksocket
    return 0



#----------------------------------------------------------------------
# create wp
#----------------------------------------------------------------------
def wp_client():
    import wordpress2
    url = options['url']
    wp = wordpress2.WordPress(url, options['user'], options['passwd'])
    return wp


#----------------------------------------------------------------------
# testing suit 
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        print(ININAME)
        print(options)
        return 0
    def test2():
        proxy('socks5://localhost/')
        proxy('http://localhost/')
        proxy('socks5://linwei:1234@localhost/')
        proxy('socks5://linwei:1234:12@localhost/')
        fatal("test")
        return 0
    def test3():
        # proxy('socks5://localhost:1080')
        url = 'https://www.google.com'
        print(ascmini.http_request(url))
    test2()



