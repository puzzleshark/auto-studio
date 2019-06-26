#!/usr/bin/env python

from distutils.core import setup

setup(name='Auto Studio',
      version='1.0',
      description='Live Recording and Video Editing Tools',
      author='Samuel Banning',
      author_email='samcbanning@gmail.com',
      packages=['pywin32', 'pyaudio', 'pydub', 'python-sounddevice', 'pysoundfile', 'moviepy'],
     )