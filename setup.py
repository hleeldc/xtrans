#! /usr/bin/env python

from distutils.core import setup

setup(name='xtrans',
      version='1.1.1',
      description='Transcription tool',
      author='Haejoong Lee',
      author_email='haejoong@ldc.upenn.edu',
      url='http://www.ldc.upenn.edu/language-resources/tools/xtrans/',
      packages=['xtrans'],
      package_dir={'xtrans': 'src'},
      scripts=['scripts/xtrans']
      )
