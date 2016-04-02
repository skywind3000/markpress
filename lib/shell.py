#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# shell.py - shell toolbox
#
# NOTE:
# for more information, please see the readme file.
#
#======================================================================
import sys, os, time

UNIX = sys.platform[:3] != 'win' and True or False


#----------------------------------------------------------------------
# call program and returns output (combination of stdout and stderr)
#----------------------------------------------------------------------
def execute(args, shell = False, capture = False):
	import sys, os
	parameters = []
	if type(args) in (type(''), type(u'')):
		import shlex
		cmd = args
		if sys.platform[:3] == 'win':
			ucs = False
			if type(cmd) == type(u''):
				cmd = cmd.encode('utf-8')
				ucs = True
			args = shlex.split(cmd.replace('\\', '\x00'))
			args = [ n.replace('\x00', '\\') for n in args ]
			if ucs:
				args = [ n.decode('utf-8') for n in args ]
		else:
			args = shlex.split(cmd)
	for n in args:
		if sys.platform[:3] != 'win':
			replace = { ' ':'\\ ', '\\':'\\\\', '\"':'\\\"', '\t':'\\t', \
				'\n':'\\n', '\r':'\\r' }
			text = ''.join([ replace.get(ch, ch) for ch in n ])
			parameters.append(text)
		else:
			if (' ' in n) or ('\t' in n) or ('"' in n): 
				parameters.append('"%s"'%(n.replace('"', ' ')))
			else:
				parameters.append(n)
	cmd = ' '.join(parameters)
	if sys.platform[:3] == 'win' and len(cmd) > 255:
		shell = False
	if shell and (not capture):
		os.system(cmd)
		return ''
	elif (not shell) and (not capture):
		import subprocess
		if 'call' in subprocess.__dict__:
			subprocess.call(args)
			return ''
	import subprocess
	if 'Popen' in subprocess.__dict__:
		if sys.platform[:3] != 'win' and shell:
			p = None
			stdin, stdouterr = os.popen4(cmd)
		else:
			p = subprocess.Popen(args, shell = shell,
					stdin = subprocess.PIPE, stdout = subprocess.PIPE, 
					stderr = subprocess.STDOUT)
			stdin, stdouterr = (p.stdin, p.stdout)
	else:
		p = None
		stdin, stdouterr = os.popen4(cmd)
	text = stdouterr.read()
	stdin.close()
	stdouterr.close()
	if p: p.wait()
	if not capture:
		sys.stdout.write(text)
		sys.stdout.flush()
		return ''
	return text


#----------------------------------------------------------------------
# call subprocess and returns retcode, stdout, stderr
#----------------------------------------------------------------------
def call(args, input = None):
	import sys, os
	parameters = []
	for n in args:
		if sys.platform[:3] != 'win':
			replace = { ' ':'\\ ', '\\':'\\\\', '\"':'\\\"', '\t':'\\t', \
				'\n':'\\n', '\r':'\\r' }
			text = ''.join([ replace.get(ch, ch) for ch in n ])
			parameters.append(text)
		else:
			if (' ' in n) or ('\t' in n) or ('"' in n): 
				parameters.append('"%s"'%(n.replace('"', ' ')))
			else:
				parameters.append(n)
	cmd = ' '.join(parameters)
	import subprocess
	if 'Popen' in subprocess.__dict__:
		p = subprocess.Popen(args, shell = False,
			stdin = subprocess.PIPE, stdout = subprocess.PIPE,
			stderr = subprocess.PIPE)
		stdin, stdout, stderr = p.stdin, p.stdout, p.stderr
	else:
		p = None
		stdin, stdout, stderr = os.popen3(cmd)
	if input != None:
		stdin.write(input)
		stdin.flush()
	exeout = stdout.read()
	exeerr = stderr.read()
	stdin.close()
	stdout.close()
	stderr.close()
	retcode = None
	if p:
		retcode = p.wait()
	return retcode, exeout, exeerr


#----------------------------------------------------------------------
# get short path in windows
#----------------------------------------------------------------------
def pathshort(path):
	if path == None:
		return None
	path = os.path.abspath(path)
	if sys.platform[:3] != 'win':
		return path
	kernel32 = None
	textdata = None
	GetShortPathName = None
	try:
		import ctypes
		kernel32 = ctypes.windll.LoadLibrary("kernel32.dll")
		textdata = ctypes.create_string_buffer('\000' * 1024)
		GetShortPathName = kernel32.GetShortPathNameA
		args = [ ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int ]
		GetShortPathName.argtypes = args
		GetShortPathName.restype = ctypes.c_uint32
	except: 
		pass
	if not GetShortPathName:
		return path
	retval = GetShortPathName(path, textdata, 1024)
	shortpath = textdata.value
	if retval <= 0:
		return ''
	return shortpath


#----------------------------------------------------------------------
# mkdir -p
#----------------------------------------------------------------------
def mkdir(path):
	import sys, os
	unix = sys.platform[:3] != 'win' and True or False
	path = os.path.abspath(path)
	if os.path.exists(path):
		return False
	name = ''
	part = os.path.abspath(path).replace('\\', '/').split('/')
	if unix:
		name = '/'
	if (not unix) and (path[1:2] == ':'):
		part[0] += '/'
	for n in part:
		name = os.path.abspath(os.path.join(name, n))
		if not os.path.exists(name):
			os.mkdir(name)
	return True


#----------------------------------------------------------------------
# rm -rf
#----------------------------------------------------------------------
def rmtree(path, ignore_error = False, onerror = None):
	import shutil
	shutil.rmtree(path, ignore_error, onerror)

#----------------------------------------------------------------------
# which
#----------------------------------------------------------------------
def which(name, prefix = None, postfix = None):
	if not prefix:
		prefix = []
	if not postfix:
		postfix = []
	PATH = os.environ.get('PATH', '').split(UNIX and ':' or ';')
	search = prefix + PATH + postfix
	for path in search:
		fullname = os.path.join(path, name)
		if os.path.exists(fullname):
			return fullname
	return None

#----------------------------------------------------------------------
# search exe
#----------------------------------------------------------------------
def search_exe(exename):
	path = which(exename)
	if path == None:
		return None
	return pathshort(path)


#----------------------------------------------------------------------
# config load
#----------------------------------------------------------------------
def load_config(path):
	import json
	try:
		text = open(path, 'r').read()
		return json.loads(text, encoding = "utf-8")
	except:
		return None
	return None


#----------------------------------------------------------------------
# config save
#----------------------------------------------------------------------
def save_config(path, obj):
	import json
	text = json.dumps(obj, indent = 4, encoding = "utf-8") + '\n'
	open(path, 'w').write(text)


#----------------------------------------------------------------------
# wget
#----------------------------------------------------------------------
def httpget(url):
	if 1:
		import urllib
		try: 
			content = urllib.urlopen(url).read()
		except:
			return None
	else:
		import urllib2
		try:
			content = urllib2.urlopen(url).read()
		except urllib2.URLError, e:
			return None
	return content


#----------------------------------------------------------------------
# timestamp
#----------------------------------------------------------------------
def timestamp(ts = None, onlyday = False):
	import time
	if not ts: ts = time.time()
	if onlyday:
		time.strftime('%Y%m%d', time.localtime(ts))
	return time.strftime('%Y%m%d%H%M%S', time.localtime(ts))


#----------------------------------------------------------------------
# timestamp
#----------------------------------------------------------------------
def readts(ts, onlyday = False):
	if onlyday: ts += '000000'
	try: return time.mktime(time.strptime(ts, '%Y%m%d%H%M%S'))
	except: pass
	return 0


#----------------------------------------------------------------------
# DNS Check
#----------------------------------------------------------------------
def checkip():
	url = 'http://ddns.oray.com/checkip'
	return httpget(url)


#----------------------------------------------------------------------
# DNS update
#----------------------------------------------------------------------
def ddns_oray_up(user, passwd, hostname, ip = None):
	user = user.replace('/', ' ').replace(':', ' ').replace('@', '@')
	passwd = passwd.replace('/', ' ').replace(':', ' ').replace('@', '@')
	url = 'http://%s:%s@ddns.oray.com/ph/update?hostname=%s'
	url = url%(user, passwd, hostname)
	if ip:
		url += '&myip=' + ip
	return httpget(url)

#----------------------------------------------------------------------
# DNS update
#----------------------------------------------------------------------
def ddns_noip_up(user, passwd, hostname, ip = None):
	user = user.replace('/', ' ').replace(':', ' ').replace('@', '@')
	passwd = passwd.replace('/', ' ').replace(':', ' ').replace('@', '@')
	url = 'http://%s:%s@dynupdate.no-ip.com/nic/update?hostname=%s'
	url = url%(user, passwd, hostname)
	if ip:
		url += '&myip=' + ip
	return httpget(url)


#----------------------------------------------------------------------
# html escape
#----------------------------------------------------------------------
def escape(s):
	import cgi
	return cgi.escape(s, True).replace('\n', "<br>\n")


#----------------------------------------------------------------------
# 输出二进制
#----------------------------------------------------------------------
def print_binary(data, char = False):
	content = ''
	charset = ''
	lines = []
	for i in xrange(len(data)):
		ascii = ord(data[i])
		if i % 16 == 0: content += '%04X  '%i
		content += '%02X'%ascii
		content += ((i & 15) == 7) and '-' or ' '
		if (ascii >= 0x20) and (ascii < 0x7f): charset += data[i]
		else: charset += '.'
		if (i % 16 == 15): 
			lines.append(content + ' ' + charset)
			content, charset = '', ''
	if len(content) < 56: content += ' ' * (54 - len(content))
	lines.append(content + ' ' + charset)
	limit = char and 100 or 54
	for n in lines: print n[:limit]
	return 0



#----------------------------------------------------------------------
# 输出调用栈
#----------------------------------------------------------------------
def print_traceback():
	import cStringIO, traceback
	sio = cStringIO.StringIO()
	traceback.print_exc(file = sio)
	for line in sio.getvalue().split('\n'):
		print line
	return 0


#----------------------------------------------------------------------
# returns last n lines of file
#----------------------------------------------------------------------
def tail(filename, need = 10):
	if type(filename) in (type(''), type(u'')):
		try:
			fp = open(filename, 'rb+')
		except:
			return None
	else:
		fp = filename
	lines = []
	fp.seek(0, os.SEEK_END)
	length = fp.tell()
	block = 1024
	position = length
	while 1:
		newpos = position - block
		if newpos < 0: newpos = 0
		canread = position - newpos
		if canread <= 0: 
			break
		fp.seek(newpos, os.SEEK_SET)
		text = fp.read(canread)
		#print 'read', repr(text)
		if len(text) == 0 or text == None:
			break
		newlines = text.split('\n')
		if len(lines) > 0:
			newlines[-1] = newlines[-1] + lines[0]
			lines = lines[1:]
		lines = newlines + lines
		if len(lines) > need + 1:
			break
		position = newpos
	if fp != filename:
		try:
			fp.close()
			fp = None
		except:
			pass
	return '\n'.join(lines[-need:])


#----------------------------------------------------------------------
# returns first n lines of file
#----------------------------------------------------------------------
def head(filename, need = 10):
	if type(filename) in (type(''), type(u'')):
		try:
			fp = open(filename, 'rb+')
		except:
			return None
	else:
		fp = filename
	lines = []
	block = 1024
	while 1:
		canread = block
		if canread <= 0: 
			break
		text = fp.read(canread)
		#print 'read', repr(text)
		if len(text) == 0 or text == None:
			break
		newlines = text.split('\n')
		if len(lines) > 0:
			lines[-1] = lines[-1] + newlines[0]
			newlines = newlines[1:]
		lines = lines + newlines
		if len(lines) > need + 1:
			break
	if fp != filename:
		try:
			fp.close()
			fp = None
		except:
			pass
	return '\n'.join(lines[:need])


#----------------------------------------------------------------------
# returns lines (characters end up with '\n'), returns next position
#----------------------------------------------------------------------
def between(filename, start = 0, stop = -1):
	if type(filename) in (type(''), type(u'')):
		try:
			fp = open(filename, 'rb+')
		except:
			return -1, None
	else:
		fp = filename
	if stop < 0:
		fp.seek(0, os.SEEK_END)
		stop = fp.tell()
	fp.seek(start, os.SEEK_SET)
	need = stop - start
	text = fp.read(need)
	if fp != filename:
		try:
			fp.close()
			fp = None
		except:
			pass
	if len(text) == 0:
		return start, None
	pos = text.rfind('\n')
	if pos < 0:
		return start, None
	text = text[:pos + 1]
	return start + len(text), text


#----------------------------------------------------------------------
# SVN
#----------------------------------------------------------------------
_EXE_SVN = search_exe('svn' + (UNIX == False and '.exe' or ''))
_EXE_SVNLOOK = search_exe('svnlook' + (UNIX == False and '.exe' or ''))

def svn(args, shell = False, capture = False):
	if not _EXE_SVN:
		sys.stderr.write('not find svn in environ PATH')
		return None
	return execute([_EXE_SVN] + args, shell, capture)

def svnlook(args, shell = False, capture = False):
	if not _EXE_SVNLOOK:
		sys.stderr.write('not find svnlook in environ PATH')
		return None
	return execute([_EXE_SVNLOOK] + args, shell, capture)

def svn_cat(url, username = None, password = None, revision = None):
	if not _EXE_SVN:
		sys.stderr.write('not find svn in environ PATH')
		return None
	args = [_EXE_SVN, 'cat']
	if username != None:
		args += ['--username', username]
	if password != None:
		args += ['--password', password]
	if revision != None:
		args += ['--revision', revision]
	args += ['--non-interactive', '--no-auth-cache']
	args += [url]
	code, out, err = call(args)
	if code != 0:
		sys.stderr.write('svn cat error:\n%s\n'%err)
		sys.stderr.flush()
		return None
	return out

def svnlook_youngest(repos):
	result = svnlook(['youngest', repos], capture = True)
	if result == None:
		return None
	revision = -1
	try:
		revision = int(result)
	except:
		revision = None
	return revision

def svnlook_cat(repos, filepath, revision = None):
	if not _EXE_SVNLOOK:
		sys.stderr.write('not find svnlook in environ PATH')
		return None
	args = [ _EXE_SVNLOOK, 'cat' ]
	if revision != None:
		args += [ '-r', str(revision) ]
	code, out, err = call(args + [repos, filepath])
	if code != 0:
		sys.stderr.write('svnlook error:\n%s\n'%err)
		sys.stderr.flush()
		return None
	return out


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':
	def test1():
		args = ['test 2/testargs.exe', 'hello world ! "no i"', 'asdf\\ asdf']
		n = execute(args, False, True)
		print 'output:'
		print n
		print '-' * 20
		import subprocess
		subprocess.call(args)
	def test2():
		cmd = '"./testargs.exe" "Hello World ! "no"" "asdf\\ asdf" -I"d:\program files\python25"'
		print execute(cmd, False, False)
	def test3():
		print pathshort('c:\\program files')
	def test4():
		obj = { 'x':1, u'y\u2012':2, 'array':[1,2,3,4,5], 'dict':{'a':3, 'b':4}}
		import json
		text = json.dumps(obj, indent = 4, encoding="utf-8")
		print json.loads(text)
		return 0
	def test5():
		#print ddns_noip_up('skywind3000', '??', 'skywind3000.ddns.net')
		#print ddns_oray_up('skywind3000', '??', 'skywind3000.eicp.net')
		print httpget('http://www.163.com/adsf')
	# shcmd.py
	# shlib.py
	# shlib.py
	# coresh.py system.py
	# shkit.py shset.py osset.py kitos.py 
	# oskit.py shellkit.py shellos shells.py
	test1()




