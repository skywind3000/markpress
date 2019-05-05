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

    # post['id']: integer uid of the post
    # post['content']: string content 
    # post['title']: string title
    # post['status']: string of draft, private, publish
    # post['category']: list
    # post['tag']: list
    def __convert_post (self, post):
        newpost = wordpress_xmlrpc.WordPressPost()
        if post:
            if 'id' in post:
                newpost.id = post['id']
            if 'title' in post:
                newpost.title = post['title']
            newpost.content = post.get('content', '')
            newpost.post_status = 'draft'
            if post.get('status'):
                newpost.post_status = post['status']
            cats = post.get('category')
            tags = post.get('tag')
            if cats or tags:
                newpost.terms_names = {}
                if cats:
                    newpost.terms_names['category'] = cats
                if tags:
                    newpost.terms_names['post_tag'] = tags
        else:
            newpost.post_status = 'draft'
            newpost.content = ''
        return newpost

    def new_post (self, post = None):
        newpost = self.__convert_post(post)
        action = wordpress_xmlrpc.methods.posts.NewPost(newpost)
        pid = self._client.call(action)
        return pid

    def edit_post (self, post):
        if 'id' not in post:
            raise ValueError('missing id in post')
        newpost = self.__convert_post(post)
        pid = post['id']
        action = wordpress_xmlrpc.methods.posts.EditPost(pid, newpost)
        return self._client.call(action)


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




