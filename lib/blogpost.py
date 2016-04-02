#!/usr/bin/env python
"""
Wordpress command-line weblog client for AsciiDoc.

Copyright: Stuart Rackham (c) 2008
License:   MIT
Email:     srackham@gmail.com

"""

# Suppress warning: "the md5 module is deprecated; use hashlib instead"
import warnings
warnings.simplefilter('ignore',DeprecationWarning)

import sys
import os
import time
import StringIO
import re
import xmlrpclib
import pickle
import md5
import calendar
import subprocess

import wordpresslib # http://www.blackbirdblog.it/programmazione/progetti/28
import asciidocapi


VERSION = '0.9.6'
PROG = os.path.basename(os.path.splitext(__file__)[0])


######################################################################
# Configuration file parameters.
# Create a separate configuration file named .blogpost in your $HOME
# directory or use the --conf-file option (see the
# blogpost_example.conf example).
# Alternatively you could just edit the values below.
######################################################################

URL = None      # Wordpress XML-RPC URL (don't forget to append /xmlrpc.php)
USERNAME = None # Wordpress login name.
PASSWORD = None # Wordpress password.


######################################################################
# End of configuration file parameters.
######################################################################


#####################
# Utility functions #
#####################

class Namespace(object):
    """
    Ad-hoc namespace.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    # This is here so unpickling <0.9.1 cache files still works.
    def __setstate__(self, state):
        self.categories = []        # Attribute added at version 0.9.1
        self.__dict__.update(state)
        self.__class__ = Cache      # Cache class name change in 0.9.1

def errmsg(msg):
    sys.stderr.write(('%s: %s\n' % (PROG,msg)).encode(sys.stderr.encoding))

def infomsg(msg):
    print '%s: %s' % (PROG,msg)

def warning(msg):
    infomsg('WARNING: '+msg)

def die(msg):
    errmsg('ERROR: %s' % msg)
    sys.exit(1)

def verbose(msg):
    if OPTIONS.verbose or OPTIONS.dry_run:
        infomsg(msg)

def load_conf(conf_file):
    """
    Import optional configuration file which is used to override global
    configuration settings.
    """
    execfile(conf_file, globals())

def shell(cmd):
    '''
    Execute command cmd in shell and return tuple
    (stdoutdata, stderrdata, returncode).
    An error terminates the application.
    '''
    verbose('executing: %s' % cmd)
#    if OPTIONS.dry_run:
#        return
    stdout = stderr = subprocess.PIPE
    try:
        popen = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, shell=True)
    except OSError, e:
        die('failed: %s: %s' % (cmd, e))
    stdoutdata, stderrdata = popen.communicate()
    if OPTIONS.verbose:
        print stdoutdata
        print stderrdata
    if popen.returncode != 0:
        die('%s returned non-zero exit status %d' % (cmd, popen.returncode))
    return (stdoutdata, stderrdata, popen.returncode)


###########
# Globals #
###########

OPTIONS = None  # Parsed command-line options OptionParser object.


####################
# Application code #
####################

class BlogpostException(Exception): pass

class Media(object):

    def __init__(self, filename):
        self.filename = filename # Client file name.
        self.checksum = None     # Client file MD5 checksum.
        self.url = None          # WordPress media file URL.

    def upload(self, blog):
        """
        Upload media file to WordPress server if it is new or has changed.
        """
        checksum = md5.new(open(self.filename,'rb').read()).hexdigest()
        if not (blog.options.force_media
                or self.checksum is None
                or self.checksum != checksum):
            infomsg('skipping unmodified: %s' % self.filename)
        else:
            infomsg('uploading: %s...' % self.filename)
            if not blog.options.dry_run:
                self.url =  blog.server.newMediaObject(self.filename)
                infomsg('url: %s' % self.url)
            else:
                self.url = self.filename  # Dummy value for debugging.
            self.checksum = checksum


class Cache(Namespace):
    """
    Structure for pickled blogpost cache file data.
    """
    pass


class Blogpost(object):

    # Valid blog parameter names.
    PARAMETER_NAMES = ('categories','status','title','doctype','posttype')

    def __init__(self, server_url, username, password, options):
        # options contains the command-line options attributes.
        self.options = options
        # Server-side blog parameters.
        self.url = None
        self.id = None
        self.title = None
        self.status = None  # Publication status ('published','unpublished').
        self.post_type = None   # 'post' or 'page'.
        # DEPRECATED: doctype 'html'
        self.doctype = None     # AsciiDoc doctype: 'article','book', 'manpage'.
        self.created_at = None  # Seconds since epoch in UTC.
        self.updated_at = None  # Seconds since epoch in UTC.
        self.media = {}  # Contains Media objects keyed by document src path.
        self.categories = []    # List of category names.
        # Client-side blog data.
        self.blog_file = None
        self.checksum = None    # self.blog_file MD5 checksum.
        self.cache_file = None  # Cache file containing persistant blog data.
        self.media_dir = None
        self.content = None     # File-like object containing blog content.
        self.parameters = {}    # AsciiDoc attribute parameter values.
        # XML-RPC server.
        self.server = None              # wordpresslib.WordPressClient.
        self.server_url = server_url    # WordPress XML-RPC server URL.
        self.username = username        # WordPress account user name.
        self.password = password        # WordPress account password.
        verbose('wordpress server: %s:%s@%s' %
            (self.username, self.password, self.server_url))
        self.server = wordpresslib.WordPressClient(
            self.server_url, self.username, self.password, self.options.proxy)
        self.server.selectBlog(0)

    def docformat(self):
        if os.path.splitext(self.blog_file)[1].lower() in ('.htm','.html'):
            return 'html'
        elif os.path.splitext(self.blog_file)[1].lower() == '.rmu':
            return 'rimu'
        else:
            return 'asciidoc'

    def is_page(self):
        return self.post_type == 'page'

    def is_published(self):
        return self.status == 'published'

    def set_blog_file(self, blog_file):
        if blog_file is not None:
            self.blog_file = blog_file
            if self.media_dir is None:
                self.media_dir = os.path.abspath(os.path.dirname(blog_file))
            self.cache_file = os.path.splitext(blog_file)[0] + '.blogpost'

    def set_title_from_blog_file(self):
        """
        Set title attribute from title in AsciiDoc blog file.
        """
        if self.docformat() == 'html':
            # Cannot reliably search adhoc HTML source for title.
            return
        if self.docformat() == 'rimu':
            for line in self.content:
                # Look for h1 title in first line.
                mo = re.match(r'<h1>(.+)</h1>', line)
                if mo:
                    self.title = mo.group(1)
                break
        else:   # AsciiDoc document.
            #TODO: Skip leading comment blocks.
            for line in open(self.blog_file):
                # Skip blank lines and comment lines.
                if not re.match(r'(^//)|(^\s*$)', line):
                    self.title = line.strip()
                    if self.title.startswith('= '):
                        self.title = line[2:].strip()
                    break

    def asciidoc2html(self):
        """
        Convert AsciiDoc blog_file to Wordpress compatible HTML content.
        """
        asciidoc = asciidocapi.AsciiDocAPI()
        asciidoc.options('--no-header-footer')
        asciidoc.options('--doctype', self.doctype)
        asciidoc.options('--attribute', 'blogpost')
        for attr in OPTIONS.attributes:
            asciidoc.options('--attribute', attr)
        for opt in OPTIONS.asciidoc_opts:
            print '%r' % opt
            opt = opt.partition(' ')
            if opt[2]:
                s = opt[2]
                s = s.strip()
                if (s.startswith('"') and s.endswith('"')
                        or s.startswith("'") and s.endswith("'")):
                    # Strip quotes.
                    s = s[1:-1]
                asciidoc.options(opt[0], s)
            else:
                asciidoc.options(opt[0])
        if OPTIONS.verbose > 1:
            asciidoc.options('--verbose')
        verbose('asciidoc: options: %r' % asciidoc.options.values)
        outfile = StringIO.StringIO()
        asciidoc.execute(self.blog_file, outfile, backend='wordpress')
        result = outfile.getvalue()
        result = unicode(result,'utf8')
        self.content = StringIO.StringIO(result.encode('utf8'))
        for s in asciidoc.messages:
            infomsg('asciidoc: %s' % s)

    def rimu2html(self):
        html = shell('rimuc "%s"' % self.blog_file)[0]
        self.content = StringIO.StringIO(html)

    def sanitize_html(self):
        """
        Convert HTML content to HTML that plays well with Wordpress.
        This involves removing all line breaks apart from those in
        <pre></pre> blocks.
        """
        result = ''
        firstline = True
        for line in self.content:
            if firstline and line and re.match(r'^<h1>.*</h1>$', line):
                # If the first line is an h1 header drop it because
                # Wordpress generates its own post title.
                # This applies to Rimu generated documents.
                pass
            elif line.startswith('<pre'):
                line = ' ' + line
                while '</pre>' not in line:
                    result += line
                    line = self.content.next()
                result += line
            elif line.startswith('src="data:'):
                line = ' ' + line
                while not line.strip().endswith('">'):
                    result += line
                    line = self.content.next()
                result += line
            else:
                result += ' ' + line.strip()
            if firstline: firstline = False
        self.content = StringIO.StringIO(result)

    def load_cache(self):
        """
        Load cache file and update self with cache data.
        """
        if self.cache_file is not None and os.path.isfile(self.cache_file):
            verbose('reading cache: %s' % self.cache_file)
            cache = pickle.load(open(self.cache_file))
            self.url = cache.url
            self.id = cache.id
            self.title = cache.title
            self.status = cache.status
            self.post_type = cache.post_type
            self.doctype = cache.doctype
            # DEPRECATED: doctype 'html'
            if self.doctype == 'html':
                self.doctype = 'article'
            self.created_at = cache.created_at
            self.updated_at = cache.updated_at
            self.media = cache.media
            self.checksum = cache.checksum
            self.categories = cache.categories

    def save_cache(self):
        """
        Write cache file.
        """
        if self.cache_file is not None:
            verbose('writing cache: %s' % self.cache_file)
            if not self.options.dry_run:
                cache = Cache(
                        url = self.url,
                        id = self.id,
                        title = self.title,
                        status = self.status,
                        post_type = self.post_type,
                        doctype = self.doctype,
                        created_at = self.created_at,
                        updated_at = self.updated_at,
                        media = self.media,
                        checksum = self.checksum,
                        categories = self.categories,
                    )
                f = open(self.cache_file, 'w')
                try:
                    pickle.dump(cache, f)
                finally:
                    f.close()

    def delete_cache(self):
        """
        Delete cache file.
        """
        if self.cache_file is not None and os.path.isfile(self.cache_file):
            infomsg('deleting cache file: %s' % self.cache_file)
            if not self.options.dry_run:
                os.unlink(self.cache_file)

    def get_parameters(self):
        '''
        Load blogpost parameters from AsciiDoc or Rimu blogpost file.
        Check attribute value validity.
        '''
        def check_value(*valid_values):
            if value not in valid_values:
                die('%s: line %d: invalid attribute value: blogpost-%s: %s' %
                    (os.path.basename(self.blog_file), lineno, name, value))

        if self.blog_file is None or self.docformat() == 'html':
            return
        if self.docformat() == 'rimu':
            reo = re.compile(r"^\{blogpost-(?P<name>[-\w]+)\}\s*=\s*'(?P<value>.*)'$")
        else:
            reo = re.compile(r':blogpost-(?P<name>[-\w]+):\s+(?P<value>.*)')
        lineno = 1
        for line in open(self.blog_file):
            mo = re.match(reo, line)
            if mo:
                name = mo.group('name')
                value = mo.group('value').strip()
                if name in self.PARAMETER_NAMES:
                    self.parameters[name] = value
                else:
                    warning('%s: line %d: invalid attribute name: blogpost-%s' %
                            (os.path.basename(self.blog_file), lineno, name))
                if name == 'status':
                    check_value('published','unpublished')
                elif name == 'doctype':
                    check_value('article','book','manpage')
                elif name == 'posttype':
                    check_value('page','post')
            lineno += 1

    def check_mandatory_parameters(self):
        '''
        Check we have the parameters required by the --mandatory-parameters option.
        '''
        if OPTIONS.mandatory_parameters:
            for name in OPTIONS.mandatory_parameters.split(','):
                if name not in self.PARAMETER_NAMES:
                    die('illegal --mandatory-parameters name: %s' % name)
                if name not in self.parameters:
                    die('%s: missing required attribute: blogpost-%s' %
                        (os.path.basename(self.blog_file), name))

    def process_media(self):
        """
        Upload images referenced in the HTML content and replace content urls
        with WordPress urls.

        Source urls are considered relative to self.media_dir.
        Processes <a> and <img> tags provided they reference files with
        valid media file name extensions.

        Caches the names and checksum of uploaded files in self.cache_file.  If
        self.cache_file is None then caching is not used and no cache file
        written.
        """
        # All these extensions may not be supported by your WordPress server,
        # Check with your hoster if you get an 'Invalid file type' error.
        media_exts = (
            'gif','jpg','jpeg','png',
            'pdf','doc','odt',
            'mp3','ogg','wav','m4a','mov','wmv','avi','mpg',
        )
        result = StringIO.StringIO()
        rexp = re.compile(r'(?i)<(?P<tag>(a\b[^>]* href)|(img\b[^>]* src))="(?P<src>.+?)"')
        for line in self.content:
            lineout = ''
            while True:
                mo = rexp.search(line)
                if not mo: break
                tag = mo.group('tag')
                src = mo.group('src')
                if src.startswith('data:'): continue    # Skip embedded images.
                url = src
                if os.path.splitext(src)[1][1:].lower() in media_exts:
                    media_obj = self.media.get(src)
                    media_file = os.path.join(self.media_dir, src)
                    if not os.path.isfile(media_file):
                        if media_obj:
                            url =  media_obj.url
                            infomsg('missing media file: %s' % media_file)
                        else:
                            url = src
                    else:
                        if not media_obj:
                            media_obj = Media(media_file)
                            self.media[src] = media_obj
                        media_obj.upload(self)
                        url =  media_obj.url
                        self.updated_at = int(time.time())
                lineout += line[:mo.start()] + ('<%s="%s"' % (tag, url))
                line = line[mo.end():]
            lineout += line
            result.write(lineout)
        result.seek(0)
        self.content = result

    def get_post(self):
        """
        Return  wordpresslib.WordPressPost with ID self.id from Wordpress
        server.
        Sets self.id, self.title, self.url, self.created_at.
        """
        verbose('getting %s %s...' % (self.post_type, self.id))
        if self.options.dry_run:
            post = wordpresslib.WordPressPost() # Stub.
        else:
            if self.is_page():
                post = self.server.getPage(self.id)
            else:
                post = self.server.getPost(self.id)
        self.id = post.id
        self.url = post.permaLink
        self.categories = post.categories
        # UTC struct_time to UTC timestamp.
        if not self.options.dry_run:
            self.created_at = calendar.timegm(post.date)
        else:
            self.created_at = time.time()   # Dummy current time.
        return post

    def info(self):
        """
        Print post cache information.
        """
        print 'title:      %s' % self.title
        print 'id:         %s' % self.id
        print 'url:        %s' % self.url
        if not self.is_page():
            print 'categories: %s' % ','.join(self.categories)
        print 'status:     %s' % self.status
        print 'type:       %s' % self.post_type
        print 'doctype:    %s' % self.doctype
        print 'created:    %s' % time.strftime('%c',
                time.localtime(self.created_at))
        print 'updated:    %s' % time.strftime('%c',
                time.localtime(self.updated_at))
        for media_obj in self.media.values():
            print 'media:      %s' % media_obj.url

    def list(self):
        """
        List recent posts.
        Information from WordPress server not from client-side cache.
        """
        if self.is_page():
            posts = self.server.getRecentPages()
        else:
            posts = self.server.getRecentPosts(20)
        for post in posts:
            print 'title:      %s' % post.title
            print 'id:         %s' % post.id
            print 'url:        %s' % post.permaLink
            print 'type:       %s' % self.post_type
            if not self.is_page():
                print 'categories: %s' % ','.join(post.categories)
            # Convert UTC to local time.
            print 'created:    %s' % \
                time.strftime('%c', time.localtime(calendar.timegm(post.date)))
            print

    def delete(self):
        """
        Delete post with ID self.id.
        """
        assert(self.id is not None)
        infomsg('deleting post %d...' % self.id)
        if not self.options.dry_run:
            if self.is_page():
                if not self.server.deletePage(self.id):
                    die('failed to delete page %d' % self.id)
            else:
                if not self.server.deletePost(self.id):
                    die('failed to delete post %d' % self.id)
        self.delete_cache()

    # DEPRECATED: create and update commands.
    def create(self):
        assert(self.id is None)
        self.post()

    # DEPRECATED: create and update commands.
    def update(self):
        assert(self.id is not None)
        self.post()

    def dump(self):
        if self.docformat() == 'rimu':
            self.rimu2html()
        else:
            self.asciidoc2html()
        print self.content.read()

    def post(self):
        """
        Update an existing Wordpress post if post_id is not None,
        else create a new post.
        """
        # Create wordpresslib.WordPressPost object.
        if self.id is not None:
            post = self.get_post()
        else:
            post = wordpresslib.WordPressPost()
        # Generate blog content from blog file.
        if self.docformat() == 'html':
            self.content = open(self.blog_file)
        elif self.docformat() == 'rimu':
            self.rimu2html()
        else:
            self.asciidoc2html()
        if not self.title:
            self.set_title_from_blog_file()
        if not self.title:
            die('missing title: use --title option')
        post.title = self.title
        # Conditionally upload media files.
        if self.options.media:
            self.process_media()
        # Make HTML WordPress friendly.
        self.sanitize_html()
        # Set post content.
        s = re.split(r'<!--\s*more\s*-->', self.content.read(), maxsplit=1)
        post.description = s[0]
        if len(s) == 2:
            post.textMore = s[1]
        # Create/update post.
        # Only update if blog file has changed.
        checksum = md5.new(open(self.blog_file,'rb').read()).hexdigest()
        if not (self.options.force
                or self.checksum is None
                or self.checksum != checksum):
            infomsg('skipping unmodified: %s' % self.blog_file)
        else:
            self.checksum = checksum
            action = 'updating' if self.id else 'creating'
            infomsg("%s %s %s '%s'..." % \
                    (action, self.status, self.post_type, self.title))
            if not self.options.dry_run:
                if self.id is None:
                    if self.is_page():
                        self.id = self.server.newPage(post, self.is_published())
                    else:
                        self.id = self.server.newPost(post, self.is_published())
                else:
                    if self.is_page():
                        self.server.editPage(self.id, post, self.is_published())
                    else:
                        self.server.editPost(self.id, post, self.is_published())
            infomsg('id: %s' % self.id)
            # Get post so we can find what it's url and creation date is.
            post = self.get_post()
            infomsg('url: %s' % post.permaLink)
            self.updated_at = int(time.time())
        self.save_cache()

    def list_categories(self):
        """
        Print alphabetized list of weblog categories.
        """
        categories = self.server.getCategoryList()
        categories = sorted(categories,
            lambda x,y: cmp(x.name.lower(), y.name.lower()))
        for cat in categories:
            print '%s (%s)' % (cat.name, cat.id)

    def set_categories(self):
        """
        Set weblog post categories based on --categories option value.
        """
        def get_cat(name, categories):
            """
            Return first category with matching name (case insensitive).
            Return None if not found.
            """
            for cat in categories:
                if name.lower() == cat.name.lower():
                    return cat

        def del_cat(id, categories):
            """
            Delete category with id from categories list.
            """
            for i,cat in enumerate(categories):
                if cat.id == id:
                    del categories[i]
                    break

        def new_cat(name):
            """
            Add a new weblog category.
            """
            infomsg('creating new category: %s...' % name)
            cat = wordpresslib.WordPressCategory()
            cat.name = name
            if not self.options.dry_run:
                cat.id = self.server.newCategory(name)
            return cat

        all_cats = self.server.getCategoryList()
        post_cats = list(self.server.getPostCategories(self.id))
        opt_cats = OPTIONS.categories.strip()
        if opt_cats:
            minus = opt_cats.startswith('-')
            plus = opt_cats.startswith('+')
            if opt_cats[0] in '+-':
                opt_cats = opt_cats[1:]
            opt_cats = [s.strip() for s in opt_cats.split(',')]
            if minus:
                for name in opt_cats:
                    cat = get_cat(name, all_cats)
                    if not cat:
                        die('no such category: %s' % name)
                    del_cat(cat.id, post_cats)
            elif plus:
                for name in opt_cats:
                    cat = get_cat(name, all_cats)
                    if not cat:
                        cat = new_cat(name)
                    if not get_cat(name, post_cats):
                        post_cats.append(cat)
            else:
                post_cats = []
                for name in opt_cats:
                    cat = get_cat(name, all_cats)
                    if not cat:
                        cat = new_cat(name)
                    post_cats.append(cat)
            cat_names = [cat.name for cat in post_cats]
            infomsg('assigning categories: %s' % ','.join(cat_names))
            if not self.options.dry_run:
                wp_cats = [{'categoryId': cat.id} for cat in post_cats]
                self.server.setPostCategories(self.id, wp_cats)
            self.categories = cat_names
            self.save_cache()

if __name__ != '__main__':
    # So we can import and use as a library.
    OPTIONS = Namespace(
                dry_run = False,
                verbose = False,
                media = True,
                categories = ''
            )
else:
    # DEPRECATED: create and update commands.
    long_commands = ('create','categories','delete','dump','info','list','post','update')
    short_commands = {'c':'create', 'cat':'categories', 'd':'delete', 'i':'info', 'l':'list', 'p':'post', 'u':'update'}
    description = """A Wordpress command-line weblog client for AsciiDoc. COMMAND can be one of: categories, delete, dump, info, list, post. BLOG_FILE is AsciiDoc (or optionally HTML) text file."""
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [OPTIONS] COMMAND [BLOG_FILE]',
        version='%s %s' % (PROG,VERSION),
        description=description)
    parser.add_option('-a', '--attribute',
        action='append', dest='attributes', default=[], metavar='ATTRIBUTE',
        help='set asciidoc attribute value')
    parser.add_option('--asciidoc-opt',
        action='append',dest='asciidoc_opts', default=[],
        metavar='ASCIIDOC_OPTION', help='set asciidoc command option')
    parser.add_option('-c', '--categories',
        dest='categories', default='', metavar='CATEGORIES',
        help='comma separated list of post categories')
    parser.add_option('-d', '--doctype',
        dest='doctype', default=None, metavar='DOCTYPE',
        help='document type (article, book, manpage, html)')
    parser.add_option('-f', '--conf-file',
        dest='conf_file', default=None, metavar='CONF_FILE',
        help='configuration file')
    parser.add_option('--force',
        action='store_true', dest='force', default=False,
        help='force blog file to upload')
    parser.add_option('--force-media',
        action='store_true', dest='force_media', default=False,
        help='force media files to upload')
    parser.add_option('--mandatory-parameters',
        dest='mandatory_parameters', default='', metavar='PARAMETERS',
        help='comma separated list of required attribute parameter names')
    parser.add_option('--media-dir',
        dest='media_dir', default=None, metavar='MEDIA_DIR',
        help='set location of media files')
    parser.add_option('-M', '--no-media',
        action='store_false', dest='media', default=True,
        help='do not process document media objects')
    parser.add_option('-n', '--dry-run',
        action='store_true', dest='dry_run', default=False,
        help='show what would have been done')
    if hasattr(wordpresslib.WordPressClient, 'getPage'):
        # We have patched wordpresslib module so enable --pages option.
        parser.add_option('-p', '--pages',
            action='store_true', dest='pages', default=False,
            help='apply COMMAND to weblog pages')
    parser.add_option('--post-id', type='int',
        dest='post_id', default=None, metavar='POST_ID',
        help='blog post ID number')
    parser.add_option('--proxy',
        dest='proxy', default=None, metavar='URL',
        help='set a proxy server')
    parser.add_option('-t', '--title',
        dest='title', default=None, metavar='TITLE',
        help='set post TITLE')
    parser.add_option('-u', '--unpublish',
        action='store_true', dest='unpublish', default=False,
        help='set post status to unpublished')
    parser.add_option('-U', '--publish',
        action='store_true', dest='publish', default=False,
        help='set post status to published')
    parser.add_option('-v', '--verbose',
        action='count', dest='verbose', default=0,
        help='increase verbosity')
    if len(sys.argv) == 1:
        parser.parse_args(['--help'])
    OPTIONS, args = parser.parse_args()
    if not hasattr(wordpresslib.WordPressClient, 'getPage'):
        OPTIONS.__dict__['pages'] = False
    # Validate options and command arguments.
    if OPTIONS.publish and OPTIONS.unpublish:
        die('--publish and --unpublish are mutually exclusive')
    command = args[0]
    if command in short_commands.keys():
        command = short_commands[command]
    if command not in long_commands:
        die('invalid command: %s' % command)
    blog_file = None
    if len(args) == 1 and command in ('categories','delete','list'):
        # No command arguments.
        pass
    elif len(args) == 2 and command in ('create','categories','delete','dump','info','update','post'):
        # Single command argument BLOG_FILE
        blog_file = args[1]
    else:
        die('too few or too many arguments')
    if blog_file is not None:
        if not os.path.isfile(blog_file):
            die('missing BLOG_FILE: %s' % blog_file)
        blog_file = os.path.abspath(blog_file)
    # DEPRECATED: doctype 'html'.
    if OPTIONS.doctype not in (None,'article','book','manpage','html'):
        die('invalid DOCTYPE: %s' % OPTIONS.doctype)
    if OPTIONS.categories and \
            (command not in ('create','update','categories','post')
             or not (blog_file or OPTIONS.post_id)):
        die('--categories is not applicable')
    if command == 'categories' and blog_file and not OPTIONS.categories:
        die('missing --categories option')
    # --post-id option checks.
    if command not in ('delete','update','categories','post') and OPTIONS.post_id is not None:
        die('--post-id is incompatible with %s command' % command)
    if command == 'delete':
        if blog_file is None and OPTIONS.post_id is None:
            die('specify the BLOG_FILE or use --post-id option')
        elif blog_file is not None and OPTIONS.post_id is not None:
            die('specify the BLOG_FILE or use --post-id option but not both')
    # If conf file exists in $HOME directory load it.
    home_dir = os.environ.get('HOME')
    if home_dir is not None:
        conf_file = os.path.join(home_dir, '.blogpost')
        if os.path.isfile(conf_file):
            load_conf(conf_file)
    if OPTIONS.conf_file is not None:
        if not os.path.isfile(OPTIONS.conf_file):
            die('missing configuration file: %s' % OPTIONS.conf_file)
        load_conf(OPTIONS.conf_file)
    # Validate configuration file parameters.
    if URL is None:
        die('Wordpress XML-RPC URL has not been set in configuration file')
    if USERNAME is None:
        die('Wordpress USERNAME has not been set in configuration file')
    if PASSWORD is None:
        die('Wordpress PASSWORD has not been set in configuration file')
    # Do the work.
    try:
        blog = Blogpost(URL, USERNAME, PASSWORD, OPTIONS)
        if OPTIONS.media_dir is not None:
            if not os.path.isdir(OPTIONS.media_dir):
                die('missing media directory: %s' % OPTIONS.media_dir)
            blog.media_dir = OPTIONS.media_dir
        blog.set_blog_file(blog_file)
        blog.load_cache()
        blog.get_parameters()
        blog.check_mandatory_parameters()
        blog.title = blog.parameters.get('title', blog.title)
        if OPTIONS.title is not None:
            blog.title = OPTIONS.title
        if OPTIONS.post_id is not None:
            blog.id = OPTIONS.post_id
        blog.post_type = blog.parameters.get('posttype', blog.post_type)
        if OPTIONS.pages:
            blog.post_type = 'page'
        if blog.post_type is None:
            blog.post_type = 'post'     # Default.
        blog.status = blog.parameters.get('status', blog.status)
        if OPTIONS.publish:
            blog.status = 'published'
        if OPTIONS.unpublish:
            blog.status = 'unpublished'
        if blog.status is None:
            blog.status = 'published'   # Default.
        blog.doctype = blog.parameters.get('doctype', blog.doctype)
        if OPTIONS.doctype is not None:
            blog.doctype = OPTIONS.doctype
        if blog.doctype is None:
            blog.doctype = 'article'    # Default.
        OPTIONS.categories = blog.parameters.get('categories', OPTIONS.categories)
        # Handle commands.
        if command == 'info':
            if not os.path.isfile(blog.cache_file):
                die('missing cache file: %s' % blog.cache_file)
            blog.info()
        elif command == 'categories':
            if OPTIONS.categories:
                blog.set_categories()
            else:
                blog.list_categories()
        elif command == 'list':
            blog.list()
        elif command == 'delete':
            if blog.id is None:
                die('missing cache file: specify --post-id instead')
            blog.delete()
        elif command == 'dump':
            blog.dump()
        elif command in ('post','create','update'):
            if blog.id is not None and command == 'create':
                die('document has been previously posted, use update command')
            if blog.id is None and command == 'update':
                die('missing cache file: specify --post-id instead')
            if command == 'update' or \
                    command == 'post' and blog.id is not None:
                blog.update()
            if command == 'create' or \
                    command == 'post' and blog.id is None:
                blog.create()
            if OPTIONS.categories:
                blog.set_categories()
        else:
            assert(False)
    except asciidocapi.AsciiDocError, e:
        errmsg(e.message)
        sys.exit(1)
    except wordpresslib.WordPressException, e:
        die(e.message)
    except xmlrpclib.ProtocolError, e:
        die(e)

