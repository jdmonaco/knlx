#!/usr/bin/env python

from distutils.core import setup
    
setup(      
            name="knlx",
            version="0.01",
            description="Module of functions for reading some Neuralynx files",
            long_description="Python module of functions for reading Neuralynx files for events (.Nev), video position-tracking (Pos.p), and continuous records (.Ncs); as well as an ASCII export function for position data",
            author="Joe Monaco",
            author_email="jmonaco@jhu.edu",
            url="http://jdmonaco.com/",
            platforms=['Mac OSX', 'Linux', 'Windows'],
            license='The MIT License',
            package_dir={'knlx': 'lib'},
            packages=['knlx'],
)
