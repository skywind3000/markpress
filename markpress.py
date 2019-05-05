#! /usr/bin/python
import sys
import os

PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(PATH, 'next'))

try:
    import nextpress
except:
    pass

nextpress.main()

