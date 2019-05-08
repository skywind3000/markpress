---
output: word_document
---
# MarkPress

Publish MarkDown documents to WordPress in command line.

## Preface

MarkPress is a command line tool to publish markdown posts to your WordPress blog.

## Features

- Syntax highlighting for fenced code block.
- Meta header in markdown to describe title / categories / tags.
- Using inline GraphViz scripts to generate graphics.
- Supports Proxy (HTTP/SOCKS4/SOCKS5).

## Installation

Clone the repository to some where you like:

```bash
git clone https://github.com/skywind3000/markpress.git ~/.local/app/markpress
```

Add `bin` folder in your `$PATH`, put the line below in your `.bashrc` / `.zshrc`:

```bash
export PATH="~/.local/app/markpress/bin:$PATH"
```

If you don't want to modify `$PATH`, you can create a symbol link for `markpress/bin/markpress` and put it in somewhere within your `$PATH`.

Install requirements:

```bash
sudo pip install wordpress_xmlrpc beautifulsoup4 PySocks
```

Now, command `markpress` is ready to work.


## Quick Start

First, create `config.ini` in `~/.config/markpress`:

```ini
[default]
tabsize=4

[0]
url=http://your-wordpress.com/
user=USERNAME
passwd=PASSWORD
```

Multiple sites can be defined in different section, like `[0]`, `[1]` and `[2]`. Section `0` is the default site.

After that, we can create a new document:

```bash
markpress -n mypost.md
```

MarkPress will create a new markdown document with meta header:

```
---
uuid: 1234
title:
status: draft
categories:
tags:
---
```

WordPress server will allocate a unique `uuid` for each new post, and use it for post identification. Now you can edit `mypost.md` with your favorite edit and write something like:

```
---
uuid: 1234
title: How to use asyncio in python ?
status: publish
categories: Development
tags: python, server
---
# Why you need asyncio ?

- reason 1
- reason 2
- reason 3

# Principle behind the asyncio

...
```

Don't forget to change `status` from `draft` to `publish`. At last use MarkPress to update your document to server:

```bash
markpress -u mypost.md
```

You may see the output:

```
post uuid=1234 updated: mypost.md
https://www.xxxx.com/blog/?p=1234
```

Now you can use the output url above to access your document.

For Windows, use `-o` to open the url in your favorite browser:

```bash
markpress -o mypost.md
```

That's all you need to know.

## Options

### Syntax Highlighting

When you are using fenced code block like:

`````
```cpp
int x = 10;
int y = 20;
```
`````

MarkPress will translate it to:

```html
<pre><code class="cpp">int x = 10;
int y = 20;
</code></pre>
```

A wordpress plugin "WP Code Highlight.js" can color each `<code>` tags by using [highlight.js](https://highlightjs.org/).

It supports 185 languages with 89 styles and will definitely satisfy your need:

![](images/highlight.png)

You can change the code block styles and modify css in the setting page of "WP Code Highlight.js" in your wordpress dashboard.


### MathJax

[MathJax](https://www.mathjax.org) is a JavaScript display engine for mathematics. The most easy way to use it in WordPress is using the "Simple MathJax" plugin.

By default:

- Expression within `$...$` will be rendered inline.
- Expression within `$$...$$` will be rendered in block. 

```
$\sum_{n=1}^{100} n$
```

Will be rendered as:

![](images/math1.gif)

and:

```
$$
AveP = \int_0^1 p(r) dr
$$
```

Will be rendered as:

![](images/math2.gif)
