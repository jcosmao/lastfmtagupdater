#!/usr/bin/env python

from distutils.core import setup
import os
import py2exe

def get_build():
    path = './.build'
    
    if os.path.exists(path):
            fp = open(path, 'r')
            build = eval(fp.read())
            if os.path.exists('./.increase_build'):
                    build += 1
            fp.close()
    else:
            build = 1
    
    fp = open(path, 'w')
    fp.write(str(build))
    fp.close()
    return unicode(build)

setup(name='lastfmtagextractor',
    description='LastFM Tag Extractor is a flexible utility for fetching and writing LastFM tags to your audio files',
    version='0.51.' + get_build(),
    url='http://code.google.com/p/lastfmtagextractor',
    author='Aaron McKee',
    author_email='',
    license='GPLv3',
    packages=['lastfmtagextractor'],
    data_files=['lastfm_tagger.conf', 'tagsyn.txt', 'README.txt', 'LICENSE.txt', 'artistskiplist.txt'],
    py_modules=['lastfmtagextractor'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Sound/Audio',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Programming Language :: Python'
    ],
    console=['lastfmtagextractor.py'],
    options ={ 'py2exe': { 'compressed': 1, 'optimize':2, 'bundle_files':3 } }
)
