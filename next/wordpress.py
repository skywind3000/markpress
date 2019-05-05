#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# wordpress2.py - 
#
# Created by skywind on 2019/05/04
# Last Modified: 2019/05/04 23:24:18
#
#======================================================================
from __future__ import print_function, unicode_literals
import sys
import wordpress_xmlrpc


#----------------------------------------------------------------------
# WordPress
#----------------------------------------------------------------------
class WordPress (object):

    def __init__ (self, url, username, password):
        self._url = self.__url_normalize(url)
        self._rpc = self.__parse_url(self._url)
        self._username = username
        self._password = password
        self._client = wordpress_xmlrpc.Client(self._rpc,
                self._username, self._password)

    def __url_normalize (self, url):
        if not url.startswith('https://'):
            if not url.startswith('http://'):
                url = 'http://' + url
        return url

    def __parse_url (self, url):
        if url.endswith('/xmlrpc.php'):
            return url
        if not url.endswith('/'):
            url = url + '/'
        return url + 'xmlrpc.php'

    def new_post (self):
        post = wordpress_xmlrpc.WordPressPost()
        post.content = ''
        post.post_status = 'draft'
        action = wordpress_xmlrpc.methods.posts.NewPost(post)
        post.id = self._client.call(action)
        return post.id

    def edit_post (self, post):
        if 'id' not in post:
            raise ValueError('missing id in post')
        newpost = wordpress_xmlrpc.WordPressPost()
        newpost.id = post['id']
        newpost.title = post['title']
        newpost.content = post['content']
        newpost.post_status = 'draft'
        if post.get('status'):
            # status: draft, private, publish
            newpost.post_status = post['status']
        newpost.terms_names = {}
        cats = post.get('category')
        if cats:
            newpost.term_names['category'] = cats
        tags = post.get('tag')
        if tags:
            newpost.term_names['post_tag'] = tags
        return True


#----------------------------------------------------------------------
# testing suit
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        wp = WordPress('localhost/web/blog', 'skywind', '678900')
        print(wp._rpc)
        return 0
    def test2():
        wp = WordPress('localhost/web/blog', 'skywind', '678900')
        print(wp.new_post())
        return 0
    test2()




