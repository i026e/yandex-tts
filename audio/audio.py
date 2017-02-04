#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 19:15:23 2017

@author: pavel
"""
import os
import sys
from threading import Thread
from subprocess import call

class SoundPlayer:
    RESULT_OK = "ok"
    def __init__(self, callback):
        self.callback = callback
        
        if sys.platform == 'linux':
            self._play = self._play_linux
        elif sys.platform == 'darwin':
            self._play = self._play_darwin
        else:
            self._play = self._play_windows
        
        
    def play(self, sound_path):
        thr = Thread(group=None, target = self._background_play_, args=(sound_path,))
        thr.start()
        thr.join()
        
    def _background_play_(self, sound_path):
        try:
            self._play(sound_path)
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            self.callback(e)
            return
        except RuntimeError as e:
            print("RuntimeError({0}): {1}".format(e.errno, e.strerror))
            self.callback(e)
            return
        except:
            print("Unexpected error:", sys.exc_info()[0])
            self.callback(sys.exc_info())
            return
        
            
        self.callback(self.RESULT_OK)
        
    def _play_windows(self, sound_path):
        os.system("start " + sound_path)
    def _play_linux(self, sound_path):
        call(["aplay",sound_path])
    def _play_darwin(self, sound_path):
        call(["afplay",sound_path])