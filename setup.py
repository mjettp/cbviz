#!/usr/bin/env python

from setuptools import setup, find_packages

VERSION = '0.1'

setup(name='cbviz',
      version=VERSION,
      description="Colorblindness visualization checker",
      author="Bill Flynn",
      author_email="wflynny@gmail.com",
      packages=find_packages(),
      install_requires=["numpy","matplotlib","colorspacious"],
      entry_points={
          'console_scripts': [
              'cbviz=cbviz.colorblindness:main',
              'cbviz-fast=cbviz.colorblindness:fast_main',
              ],
          },
     )
