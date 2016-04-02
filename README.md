MarkPress
---------

使用 Markdown 来再命令行写 WordPress 的感觉很不错，我整合了两个 Python 库，一个叫 blogpost，
另外一个叫做 markdown2，前者可以用来命令行发送 WordPress 文章，但是只支持 .html 或者 
asciidoc 格式来写 WordPress，因此又引入了 python 的 markdown2，合成项目：

<https://github.com/skywind3000/markpress>

但是标准 Markdown转换出来的 html 再 wordpress中高亮不正确，因此费了点时间修改了一版 markdown2
为 markdown3 ，调整了相关的样式，可以很好的在 wordpress 中显示，同时使用了 metadata，再文章中
可以指定标题和类别，使用很简单，首先克隆项目：
   
     $ git clone https://github.com/skywind3000/markpress.git

然后创建你的工程目录 myblog（用来保存文章和相关中间数据，推荐提交到版本管理系统上来），目录为：

```
myblog +- wordpress.ini  # 站点配置文件，url，用户名，密码
       +- doc            # 存放 markdown 文章源文件的目录
       +- data           # 自动生成的 postid/html等，丢失会导致重新发文
       +- images         # 保存图片的目录，文章中图片都用 "../images/*" 引用
```

<!--more-->

再 wordpress.ini 里面的 url 为 wordpress 的 xmlrpc.php 的路径：

```ini
[default]
url=http://example.com/wordpress/xmlrpc.php
username=????
password=????
```

然后就可以再 doc 下写一篇名为：doc/post.1.md 的文章了：

```
---
title: 文章的标题
categories: 文章类别
---

文章内容
```

最后使用 markpress.py 发布该文章：

```
$ cd myblog
$ python /path-to-markpress/markpress.py post.1.md
```

注意：在myblog目录下运行 markpress.py，需要再当前目录寻找 wordpress.ini ，同时指定文章
名字的时候使用 "post.1.md" 而不是 "doc/post.1.md" ，markpress会自动到doc目录下去寻找
并且再 data 目录下面生成 html 和中间数据。

如果你将 myblog 目录放入 svn/git的话，可以很好的保存你的文章源文件，注意将 doc, data, images
都放入版本管理系统（data下面每次自动生成的 html, blogpost文件也需要一起放入版本管理），而
站点配置文件：wordpress.ini 到是不一定要放入版本管理。

所有 images下面的图片在 markdown 中需要用："../images/abc.jpg" 来引用，这样转换到 data
下面的 html 也可以保持正确引用，同时上传的时候会自动判断图片是否有改动来判断是否需要上传新图片。

如此，你可以自由的用你喜爱 markdown 编辑器来离线写 WordPress 了，并且配置上快捷键一键发布，
本篇博文即使用 MarkPress 写成，十分方便。



