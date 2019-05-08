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

