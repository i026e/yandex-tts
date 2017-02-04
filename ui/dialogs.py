#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 02.02.17 11:34

@project: fb2
@author: pavel
"""

import gi
from gi.repository import Gtk

class Confirmation(Gtk.MessageDialog):
    def __init__(self, parent_window, message):
        super(Confirmation, self).__init__(parent_window,
                                        Gtk.DialogFlags.MODAL,
                                        Gtk.MessageType.QUESTION,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OK, Gtk.ResponseType.OK),
                                        message)
    def ok(self):
        response = self.run()
        self.destroy()
        return response == Gtk.ResponseType.OK

class OpenFolder(Gtk.FileChooserDialog):
    def __init__(self, parent_window, init_path):
        super(OpenFolder, self).__init__("Select folder", parent_window,
                         Gtk.FileChooserAction.SELECT_FOLDER,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OPEN,  Gtk.ResponseType.OK))
        self.set_current_folder(init_path)

    def get_folder(self):
        response = self.run()
        dir_name = self.get_filename()
        self.destroy()
        if response == Gtk.ResponseType.OK:
            return dir_name

class OpenFile(Gtk.FileChooserDialog):
    def __init__(self, parent_window):
        super(OpenFile, self).__init__("Select file", parent_window,
                                         Gtk.FileChooserAction.OPEN,
                                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                          Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    def get_file(self):
        response = self.run()
        file_name = self.get_filename()
        self.destroy()
        if response == Gtk.ResponseType.OK:
            return file_name

class About(Gtk.AboutDialog):
    def __init__(self, parent_window):
        super(About, self).__init__(transient_for=parent_window, modal=True)

    def show(self):
        self.run()
        self.destroy()

class APIKey(Gtk.MessageDialog):
    def __init__(self, parent_window, current_key, url, link_title):
        super(APIKey, self).__init__(parent_window,
                                    Gtk.DialogFlags.MODAL,
                                    Gtk.MessageType.QUESTION,
                                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OK, Gtk.ResponseType.OK),
                                    None)
        self.set_markup('Please enter <b>API key</b>:')
        secondary = "You can get one at <a href = \"{url}\"> {link_title} </a> ".format(url = url,
                                                                                       link_title = link_title)
        self.format_secondary_markup(secondary)

        self.input_form = Gtk.Entry()
        self.input_form.set_text(str(current_key))
        self.vbox.pack_end(self.input_form, True, True, 0)

    def get_key(self):
        self.show_all()
        response = self.run()
        key = self.input_form.get_text().strip()
        self.destroy()
        if response == Gtk.ResponseType.OK:
            return key


