#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# wordpress2.py - wordpress api
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
    # post['comment']: open/closed
    # post['date']: datetime object in UTC
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
            if post.get('comment'):
                newpost.comment_status = post['comment']
            if post.get('date'):
                newpost.date = post['date']
            if post.get('date_modifed'):
                newpost.date_modified = post['date_modified']
            if post.get('slug'):
                newpost.slug = post['slug']
        else:
            newpost.post_status = 'draft'
            newpost.comment_status = 'open'
            newpost.content = ''
        return newpost

    def post_new (self, post = None):
        newpost = self.__convert_post(post)
        action = wordpress_xmlrpc.methods.posts.NewPost(newpost)
        pid = self._client.call(action)
        return pid

    def post_edit (self, post):
        if 'id' not in post:
            raise ValueError('missing id in post')
        newpost = self.__convert_post(post)
        pid = post['id']
        action = wordpress_xmlrpc.methods.posts.EditPost(pid, newpost)
        return self._client.call(action)

    def post_get (self, pid):
        action = wordpress_xmlrpc.methods.posts.GetPost(pid)
        return self._client.call(action)

    # keys of query: number, offset, orderby, order(ASC/DESC), post_type
    # and post_status
    # returns list of WordPressPost instances
    def post_list (self, query):
        action = wordpress_xmlrpc.methods.posts.GetPosts(query)
        return self._client.call(action)

    # returns { 'id':xx, 'file':xx, 'url':xx, 'type':xx }
    def media_upload (self, source, name, mime = None):
        if isinstance(source, str):
            content = open(source, 'rb').read()
        if hasattr(source, 'read'):
            content = source.read()
        else:
            content = source
        if mime is None:
            if content[:3] == b'\xff\xd8\xff':
                mime = 'image/jpeg'
            elif content[:5] == b'\x89PNG\x0d':
                mime = 'image/png'
            elif content[:2] == b'\x42\x4d':
                mime = 'image/x-bmp'
            elif content[:5] == b'GIF89':
                mime = 'image/gif'
            elif content[:2] == b'\x50\x4b':
                mime = 'application/zip'
            elif content[:3] == b'\x37\x7a\xbc':
                mime = 'application/x-7z-compressed'
        data = {}
        data['name'] = name
        data['bits'] = wordpress_xmlrpc.compat.xmlrpc_client.Binary(content)
        if mime:
            data['type'] = mime
        action = wordpress_xmlrpc.methods.media.UploadFile(data)
        response = self._client.call(action)
        return response

    def media_get (self, attachment_id):
        action = wordpress_xmlrpc.methods.media.GetMediaItem(attachment_id)
        return self._client.call(action)

    # keys of query: number, offset, parent_id, mime_type
    # returns list of WordPressMedia instances
    def media_list (self, query):
        action = wordpress_xmlrpc.methods.media.GetMediaLibrary(query)
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
        pid = wp.post_new()
        post = {}
        import ascmini
        post['id'] = pid
        post['content'] = 'Now is: ' + ascmini.timestamp()
        post['title'] = 'robot'
        post['status'] = 'publish'
        post['category'] = ['life']
        post['tag'] = ['ai', 'game']
        print(wp.post_edit(post))
        return 0
    def test3():
        wp = WordPress('localhost/web/blog', 'skywind', '678900')
        post = wp.post_get(40)
        print(post)
        print(post.link)
        print(post.content)
        print(post.id)
        return 0
    def test4():
        wp = WordPress('localhost/web/blog', 'skywind', '678900')
        query = {}
        query['offset'] = 0
        for post in wp.post_list(query):
            print(post)
            print(post.link)
            print(post.date)
            print(type(post.date), post.date.timestamp())
        return 0
    test4()




