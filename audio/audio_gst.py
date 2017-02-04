#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Sep 14 17:38:42 2015

@author: pavel
"""

import os
import time
import threading
from sys import argv

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst


from urllib.parse import urljoin
from urllib.request import pathname2url


GObject.threads_init()
Gst.init(None)

class Player:
    def __init__(self, volume = 1.0, callback_on_stop=None, callback_on_progress=None):
        """ constructor
        volume[optional] : initial player volume
        callback_on_stop[optional] : function(file_url) to be called
            after record was stopped
        callback_on_progress[optional] : function(file_url, file_duration, position_so_far)
            to be called at each position update """
        self.active = False

        self.volume = volume

        self.callback_on_stop = callback_on_stop
        self.callback_on_progress = callback_on_progress

        self.track = None
        self.track_duration = None

        self.player = Gst.ElementFactory.make('playbin', 'player')
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.watch_id = self.bus.connect("message", self.message_handler)

        self.set_volume(volume)
        #self.control = Gst.Controller(src, "freq", "volume")
        #GObject.MainLoop().run()
        self.auto_polling_enabled = False

    def start_polling(self, polling_interval=1, forcedCheck = False):
        """ function to be called every polling_interval seconds if player is playing
        functions should takes as parameters file_url, track_length, current_position"""

        def poll():
            while self.auto_polling_enabled:
                time.sleep(polling_interval)
                if self.track is not None \
                and  self.is_active(forcedCheck) \
                and self.is_playing():
                    self.on_progress_update()


        if not self.auto_polling_enabled:
            self.auto_polling_enabled = True
            self.selfcheck_thread = threading.Thread(target=poll)
            self.selfcheck_thread.daemon = True
            self.selfcheck_thread.start()

            return True

        return False

    def stop_polling(self):
        self.auto_polling_enabled = False

    def close(self):
        """ destructor """
        print("destruction...")

        self.stop_polling()
        self.stop()

        #if self.bus is not None:
        self.bus.remove_signal_watch()
        self.bus.disconnect(self.watch_id)

    def _path2url(self, path):
        return urljoin('file:', pathname2url(os.path.abspath(path)))

    def load_track(self, path):
        """ add track to player
        path : path to the file
        will return url to the file"""
        if self.track is not None:
            self.stop()

        self.track = self._path2url(path)
        self.player.set_property('uri', self.track)
        return self.track


    def stop(self):
        if self.active:
            print(self.track + " stopped")
            self.player.set_state(Gst.State.NULL)
            self.active = False

            if self.callback_on_stop is not None:
                self.callback_on_stop(self.track)
        self.track_duration = None
        
    def play(self):
        """ start playing """
        print(self.track + " playing")
        self.player.set_state(Gst.State.PLAYING)
        self.active = True
        
    def pause(self):
        """ pause """
        print(self.track + " paused")
        self.player.set_state(Gst.State.PAUSED)
        
    def resume(self):
        """ resume playing """
        print(self.track + " resumed")
        self.player.set_state(Gst.State.PLAYING)
        
    def set_volume(self, volume):
        """ set track volume to value in [0.0 1.0]"""
        self.volume = volume
        self.player.set_property('volume', self.volume)
        
    def get_volume(self):
        """ get track volume """
        return self.volume
        
    def mute(self):
        """  """
        self.player.set_property('volume', 0.0)
        
    def unmute(self):
        """ """
        self.player.set_property('volume', self.volume)

    def get_duration(self):
        """ get duration in seconds"""
        if self.track_duration is None:
            self.track_duration = self.player.query_duration(Gst.Format.TIME)[1] /Gst.SECOND
        return self.track_duration
        
    def get_position(self):
        """ get position in seconds"""
        return self.player.query_position(Gst.Format.TIME)[1] /Gst.SECOND
        
    def set_position(self, position):
        """ set current position to position in seconds"""
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH
        | Gst.SeekFlags.KEY_UNIT, position * Gst.SECOND)

    def _get_state(self):
        status, state, pending = self.player.get_state(Gst.CLOCK_TIME_NONE)
        #print status, state, pending
        return state
        
    def is_active(self, forcedCheck = True):
        """ return true if is playing or on pause"""
        if forcedCheck:
            self.check_messages()
        return self.active
        
    def is_paused(self):
        return self._get_state() == Gst.State.PAUSED
        
    def is_playing(self):
        return self._get_state() == Gst.State.PLAYING

    def message_handler(self, bus, message):
        # Capture the messages on the bus and
        # set the appropriate flag.
        if message is None: return

        msgType = message.type
        print(msgType, message)
        if msgType == Gst.MessageType.ERROR:
            self.stop()

            print("Unable to play audio. Error: ", message.parse_error())
        elif msgType == Gst.MessageType.EOS:
            self.stop()

    def check_messages(self):
        """ manually check messages"""
        types = Gst.MessageType.EOS | Gst.MessageType.ERROR
        self.message_handler(self.bus ,self.bus.pop_filtered (types))

    def on_progress_update(self):
        self.callback_on_progress(self.track, self.get_duration(), self.get_position())

def play(f_names):
    f_names.append("./test.mp3")

    def callback_on_stop(file_url):
        print("end of " + file_url)

    def callback_on_progress(file_url, dur, pos):
        print(str(pos)+' / ' + str(dur))

    pl = Player(volume = 0.2, callback_on_stop=callback_on_stop)
    #pl.start_polling(forcedCheck=True)

   
    for f_name in f_names: 
        if os.path.isfile(f_name):
            print("Loading", pl.load_track(f_name))
            pl.play()
            time.sleep(1)
    
            print('Duration : '+ str(pl.get_duration()))
    
            while pl.is_active():
                print('Position : '+  str(pl.get_position()), end='\r')
                time.sleep(1)
            pl.stop()
            print()

    pl.close()



if __name__ == "__main__":
    play(argv[1:])