#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 15:41:33 2017

@author: pavel
"""
import sys
from subprocess import call

def concat(files_list, output):
    call(["ffmpeg", "-f", "concat", "-i", files_list, "-c", "copy", output])

