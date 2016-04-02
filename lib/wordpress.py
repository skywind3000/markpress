#! /usr/bin/python
#----------------------------------------------------------------------
#
# wordpress.py - wordpress 
#
# NOTE:
# for more information, please see the readme file
#
#----------------------------------------------------------------------
import sys, time, os
import markdown3
import blogpost


#----------------------------------------------------------------------
# global definition
#----------------------------------------------------------------------
def die (message):
	sys.stderr.write('%s\n'%message)
	sys.stderr.flush()
	sys.exit(1)


#----------------------------------------------------------------------
# configure
#----------------------------------------------------------------------
class configure (object):

	def __init__ (self, home = '.'):
		self._dirhome = os.path.abspath(home)
		self._ininame = self.path('wordpress.ini')
		self._inipath = ''
		self._config = {}
		self._posts = []
		self._names = []
		self._wordpress = {}
		self._update_site()
		self._update_posts()
	
	def path (self, name):
		return os.path.abspath(os.path.join(self._dirhome, name))

	def die (self, message):
		sys.stderr.write('%s\n'%message)
		sys.stderr.flush()
		sys.exit(1)
		return 0

	def _read_content (self, name):
		content = open(name, 'rb').read()
		if content[:3] == '\xef\xbb\xbf':
			content = content[3:]
		return content

	def _update_site (self):
		if not os.path.exists(self._ininame):
			self.die('missing %s\n'%self._ininame)
		import StringIO
		import ConfigParser
		sio = StringIO.StringIO(self._read_content(self._ininame))
		cp = ConfigParser.ConfigParser()
		cp.readfp(sio)
		for sect in cp.sections():
			self._config[sect] = {}
			for key, val in cp.items(sect):
				self._config[sect][key] = val.strip('\r\n\t ')
		class Object (object): pass
		self._wordpress = Object()
		self._wordpress.url = self.config('default', 'url')
		self._wordpress.username = self.config('default', 'username')
		self._wordpress.password = self.config('default', 'password')
		if not self._wordpress.url:
			self.die('can not find url in %s\n'%self._ininame)
		if not self._wordpress.username:
			self.die('can not find username in %s\n'%self._ininame)
		return 0

	def config (self, sect, key, default = None):
		if not sect in self._config:
			return default
		val = self._config[sect].get(key, default)
		return val

	def _update_posts (self):
		self._posts = []
		self._names = {}
		for fn in os.listdir(self.path('doc')):
			ext = os.path.splitext(fn)[-1].lower()
			if ext != '.md':
				continue
			class Object (object): pass
			main = os.path.splitext(fn)[0]
			post = Object()
			post.name = fn
			post.filename = {}
			post.filename['md'] = self.path('doc/' + fn)
			post.filename['html'] = self.path('data/' + main + '.html')
			post.filename['meta'] = self.path('data/' + main + '.blogpost')
			self._update_info(post)
			self._posts.append(post)
			self._names[fn] = post
		return 0

	def _update_info (self, post):
		time_md = os.stat(post.filename['md']).st_ctime
		time_html = -1
		time_meta = -1
		post.modified = False
		if os.path.exists(post.filename['html']):
			time_html = os.stat(post.filename['html']).st_ctime
			if time_html < time_md: post.modified = True
		else:
			post.modified = True
		if os.path.exists(post.filename['meta']):
			time_meta = os.stat(post.filename['meta']).st_ctime
			if time_meta < time_md: post.modified = True
		else:
			post.modified = True
		post.title = ''
		post.categories = []
		post.tags = []
		return 0

	def __getitem__ (self, index):
		if type(index) in (type(''), type(u'')):
			return self._names.get(index)
		return self._posts[index]

	def __contains__ (self, index):
		if type(index) in (type(''), type(u'')):
			return (index in self._names)
		return (index >= 0) and (index < len(self._posts))

	def __len__ (self):
		return len(self._posts)

	def __repr__ (self):
		return repr([ p.name for p in self._posts ])

	def markdown (self, post):
		content = open(post.filename['md'], 'rb').read()
		if content[:3] == '\xef\xbb\xbf':
			content = content[3:]
		content = content.decode('utf-8')
		extras = ['metadata', 'fenced-code-blocks']
		extras.append('cuddled-lists')
		extras.append('tables')
		extras.append('footnotes')
		post.html = markdown3.markdown(content, extras = extras)
		#print post.html.metadata
		post.metadata = post.html.metadata and post.html.metadata or {}
		post.title = post.metadata.get('title', '').strip('\r\n\t ')
		categories = post.metadata.get('categories', '').split(',')
		tags = post.metadata.get('tags', '').split(',')
		post.categories = []
		post.tags = []
		for n in [ n.strip() for n in categories ]:
			if n: post.categories.append(n)
		for n in [ n.strip() for n in tags ]:
			if n: post.tags.append(n)
		post.id = post.metadata.get('id', None)
		post.status = post.metadata.get('status', 'published').strip()
		return post
	
	def wordpress (self, options):
		class Object (object): pass
		opt = Object()
		opt.attributes = []
		opt.asciidoc_opts = []
		opt.categories = ''
		opt.doctype = None
		opt.conf_file = None
		opt.force = False
		opt.force_media = False
		opt.mandatory_parameters = ''
		opt.media_dir = None
		opt.media = True
		opt.dry_run = False
		opt.pages = False
		opt.id = None
		opt.proxy = None
		opt.title = None
		opt.status = None
		opt.verbose = 0
		opt.command = None 
		opt.filename = None
		import xmlrpclib
		for n in options:
			opt.__dict__[n] = options[n]
		try:
			blogpost.OPTIONS = opt
			blog = blogpost.Blogpost( \
					self._wordpress.url, \
					self._wordpress.username, \
					self._wordpress.password, \
					opt)
			blog.set_blog_file(opt.filename)
			blog.load_cache()
			blog.get_parameters()
			blog.check_mandatory_parameters()
			blog.title = blog.parameters.get('title', blog.title)
			if opt.title:
				blog.title = opt.title
			if opt.id is not None:
				blog.id = opt.id
			blog.post_type = blog.parameters.get('posttype', blog.post_type)
			if blog.post_type is None:
				blog.post_type = 'post'
			blog.status = blog.parameters.get('status', blog.status)
			if opt.status:
				blog.status = opt.status
			if blog.status is None:
				blog.status = 'published'
			blog.doctype = blog.parameters.get('doctype', blog.doctype)
			if opt.doctype is not None:
				blog.doctype = options.doctype
			if blog.doctype is None:
				blog.doctype = 'article' # default
			opt.categories = blog.parameters.get('categories', opt.categories)
			command = opt.command
			if command == 'info':
				blog.info()
			elif command == 'categories':
				if opt.categories:
					blog.set_categories()
				else:
					blog.list_categories()
			elif command == 'list':
				blog.list()
			elif command == 'delete':
				if blog.id is None:
					die('missing cache file: specify id please')
				blog.delete()
			elif command == 'dump':
				blog.dump()
			elif command in ('post', 'create', 'update'):
				if blog.id is not None and command == 'create':
					die('document has been previously posted, use update command')
				if blog.id is None and command == 'update':
					die('missing cache file: specify id instead')
				if command == 'update' or \
						command == 'post' and blog.id is not None:
					blog.update()
				if command == 'create' or \
						command == 'post' and blog.id is None:
					blog.create()
				if opt.categories:
					blog.set_categories()
			else:
				die('unknow command')
		except xmlrpclib.ProtocolError, e:
			die(e)
		return 0



#----------------------------------------------------------------------
# wordpress
#----------------------------------------------------------------------
class wordpress (object):

	def __init__ (self, home = '.'):
		self.config = configure(home)
		self.verbose = False

	def info (self, message):
		if self.verbose:
			print message
		return 0

	def warn (self, message):
		sys.stderr.write('%s\n'%message)
		sys.stderr.flush()

	def synchronize (self, name, force = False, verbose = False):
		self.verbose = verbose
		if os.path.splitext(name)[-1] != '.md':
			self.warn('can not synchronize non markdown file')
			return -1
		if not name in self.config:
			self.warn('missing doc/%s in %s'%(name, self.config._dirhome))
			return -2
		post = self.config[name]
		if post.modified == False and force == False:
			self.info('[skip: %s]'%name)
			return 0
		self.info('[synchronizing: %s]'%name)
		self.config.markdown(post)
		if not post.title:
			self.warn('missing title in %s'%(name))
			return -3
		opt = {}
		opt['title'] = post.title.encode('utf-8')
		if post.id:
			opt['title'] = post.id
		if post.categories:
			opt['categories'] = (','.join(post.categories)).encode('utf-8')
		if post.tags:
			opt['tags'] = (','.join(post.tags)).encode('utf-8')
		opt['command'] = 'post'
		self.info('writing: %s'%post.filename['html'])
		fp = open(post.filename['html'], 'wb')
		fp.write(post.html.encode('utf-8'))
		fp.close()
		opt['filename'] = post.filename['html']
		opt['status'] = post.status
		opt['force'] = force
		self.config.wordpress(opt)
		self.info('')
		return 0
		


#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------
def main(args = None):
	if args == None:
		args = sys.argv
	args = [ n for n in args ]
	import optparse
	description = 'A Wordpress command-line weblog client for markdown'
	parser = optparse.OptionParser( \
			usage='usage: %prog [OPTIONS] BLOG_FILE',
			version='1.0.0',
			description = description)
	parser.add_option('--force', action='store_true', dest='force',
			default = False, help = 'force blog file to upload')
	OPTIONS, ARGS = parser.parse_args(args)
	if len(ARGS) < 2:
		print 'missing blog_file'
		return -1
	filename = ARGS[1]
	print ARGS
	wp = wordpress()
	wp.synchronize(filename, OPTIONS.force, True)
	return 0
			


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':

	def test1():
		config = configure('.')
		print config.path('.')
		print config
		print config._wordpress.url
		print config._wordpress.username
		return 0
	
	def test2():
		wp = wordpress()
		wp.synchronize('post.3.md', True, True)
		return 0
	
	#test2()
	main()



