#! /usr/bin/python3
import sys
import os

PATH = os.path.abspath(os.path.dirname(__file__))
PATH = os.path.join(PATH, '../lib')
sys.path.append(os.path.normpath(PATH))

if 1:
    import nextpress

nextpress.main()

