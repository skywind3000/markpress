# MarkPress

Publish MarkDown documents to WordPress in command line.

## Preface

MarkPress is a command line tool to publish markdown posts to your WordPress blog.

## Features

- Syntax highlighting for fenced code block.
- Convert GraphViz script to inline SVG.

## Installation

1. Clone the repository to some where you like:

    ```bash
    git clone https://github.com/skywind3000/markpress.git ~/.local/app/markpress
    ```

2. Add `bin` folder in your `$PATH`, put the line below in your `.bashrc` / `.zshrc`:

     ```bash
     export PATH="~/.local/app/markpress/bin:$PATH"
     ```

3. Install requirements:

    ```bash
    sudo pip install wordpress_xmlrpc beautifulsoup4 PySocks
    ```

Now, command `markpress` is ready to work.


## Quick Start

