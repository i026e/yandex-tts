#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 19:11:11 2017

@author: pavel
"""
import os
import signal
import sys
import tempfile

signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, Gdk

APP = "tts.text-to-audio"
DIR = os.path.dirname(os.path.realpath(__file__))
GLADE_FILE = "ui/creator.glade"

import locale
locale.setlocale(locale.LC_ALL, '')
if os.path.isdir("../locale"):
    locale.bindtextdomain(APP, "../locale")
    locale.textdomain(APP)

from ui import dialogs
from text import text_exctractor, text_splitter
from tts import yandex_tts
import config
from audio import audio_gst
from task import task
import stat_func


class MainWindow:
    def __init__(self, builder, app, config,
                 parent_window = None,
                 report_cb = None,
                 close_on_add = False):
        self.parent_window = parent_window
        self.config = config
        self.builder = builder
        self.report_cb = report_cb
        self.close_on_add = close_on_add


        self.builder.add_from_file(GLADE_FILE)
        self.window = self.builder.get_object("main_window")
        self.window.set_application(app)

        if parent_window is not None:
            self.window.set_transient_for(parent_window)
            self.window.set_modal(True)
        else:
            self.window.connect("delete-event", app.on_quit)

        self.parameters_box = self.builder.get_object("parameters_box")
        self.book_view = self.builder.get_object("book_view")
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        
        self.init_control()
        self.init_actions()

        self.book = ""
        self.player = audio_gst.Player(volume = 0.5, callback_on_stop=print)
        
        self.splitter = text_splitter.Splitter(yandex_tts.MAX_SYMBOLS)

    def init_actions(self):
        action_listen = Gio.SimpleAction.new("listen", None)
        action_listen.connect("activate", self.on_listen)
        self.window.add_action(action_listen)

        action_add = Gio.SimpleAction.new("add", None)
        action_add.connect("activate", self.on_add)
        self.window.add_action(action_add)

        action_open = Gio.SimpleAction.new("open", None)
        action_open.connect("activate", self.on_open)
        self.window.add_action(action_open)

        action_cut = Gio.SimpleAction.new("cut", None)
        action_cut.connect("activate", self.on_cut)
        self.window.add_action(action_cut)

        action_paste = Gio.SimpleAction.new("paste", None)
        action_paste.connect("activate", self.on_paste)
        self.window.add_action(action_paste)

        action_copy = Gio.SimpleAction.new("copy", None)
        action_copy.connect("activate", self.on_copy)
        self.window.add_action(action_copy)

        action_delete = Gio.SimpleAction.new("delete", None)
        action_delete.connect("activate", self.on_delete)
        self.window.add_action(action_delete)

        action_request_api = Gio.SimpleAction.new("api", None)
        action_request_api.connect("activate", self.on_api_request)
        self.window.add_action(action_request_api)
            
    def init_control(self):
        for name, (input_type, possible_vals) in yandex_tts.PROPERTIES.items():
            default_val = yandex_tts.DEFAULT_PROPERTIES.get(name)
            val_type = yandex_tts.PROPERTIES_TYPES.get(name)
            lbl = yandex_tts.PROPERTIES_LBLS.get(name)

            val = self.config.get_value("tts", name, val_type, default_val)

            if input_type == range:
                min_, max_ = possible_vals
                self.add_scale(name, lbl, min_, max_, val)
            else:
                self.add_combobox(name, lbl, possible_vals, val)
        
    def add_combobox(self, name, lbl, possible_vals, selected_val):
        label = Gtk.Label(lbl)
        box = Gtk.ComboBoxText()
        
        for ind, val in enumerate(possible_vals):            
            box.append_text(str(val))
            
            if val == selected_val:
                box.set_active(ind)
        
        on_change = lambda box_, name_ : self.config.set_value("tts", name_, box_.get_active_text())
        box.connect("changed", on_change, name)
        self.parameters_box.pack_start(label, True, True, 0)
        self.parameters_box.pack_start(box, True, True, 0)
        
    def add_scale(self, name, lbl, min_val, max_val, selected_val):

        label = Gtk.Label(lbl)
        
        scale = Gtk.Scale()
        scale.set_draw_value(True)
        scale.set_range(min_val, max_val)
        
        step = stat_func.scale_step(min_val, max_val)
        scale.set_increments(step, 5*step)

        scale.set_value(selected_val)
        
        on_change = lambda range_, scroll_, val_, name_: self.config.set_value("tts", name_, val_)
        scale.connect("change-value", on_change, name)
        
        self.parameters_box.pack_start(label, True, True, 0)
        self.parameters_box.pack_start(scale, True, True, 0)
        
    def present(self):
        self.window.show_all()

        tts_key = self.config.get_value("tts", "key", str, "")
        if (tts_key is None) or (len(tts_key) == 0):
            self.on_api_request()


    def get_text(self):
        buffer = self.book_view.get_buffer()
        txt_start = buffer.get_start_iter()
        txt_end = buffer.get_end_iter()
        text = buffer.get_text(txt_start, txt_end, False)
        return text

    def get_book_name(self):
        if len(self.book) > 0:
            return os.path.basename(self.book)
        else:
            return "manuscript"
        
    def close(self, *args):
        self.window.destroy()

    def on_listen(self, *args):
        text = ""

        buffer = self.book_view.get_buffer()
        if buffer.get_has_selection():
            start, end = buffer.get_selection_bounds() \
                #if buffer.get_has_selection() \
            #else (buffer.get_start_iter(), buffer.get_end_iter())
            text = buffer.get_text(start, end, False)

        fmt = self.config.get_value("tts", "format", str, "")
        print(format)
        tmp = tempfile.NamedTemporaryFile(suffix = "." + fmt)
        tts = yandex_tts.Voice.new(self.config.get_group("tts"))
        
        result_path = tts.save_audio(text, tmp.name)
        if result_path is not None:
            self.player.load_track(result_path)
            self.player.play()

    def on_add(self, *args):
        text = self.get_text()
        if len(text) > 0:
            folder = self.select_folder()
            if folder is not None:
                book_name = self.get_book_name()

                task_mgr = task.TaskManager(self.config.get_value("app", "db_path",
                                                               str, config.DEFAULT_TASK_DB_FILE))

                task_params = {"tts" : self.config.get_group("tts")}
                tsk_id, tsk = task_mgr.create_task(book_name, task_params, str(folder))
                tsk_fmt = self.config.get_value("tts", "format", str, "")

                task_mgr.close()

                if tsk is not None:
                    self.fill_task(tsk, text, tsk_fmt)
                    tsk.close()

                    if self.report_cb is not None:
                        self.report_cb(tsk_id)

                if self.close_on_add:
                    self.close()

    def fill_task(self, tsk, text, fmt):
        index = 1
        for section in self.splitter.split(text):
            fname = "{ind:04d}.{fmt}".format(ind=index, fmt=fmt)
            tsk.add_line(fname, section, commit=False)
            index += 1


    def on_open(self, *args):
        book_path = dialogs.OpenFile(self.window).get_file()
        if book_path is not None:
            self.load_book(book_path)

    def on_cut(self, *args):
        buffer = self.book_view.get_buffer()
        buffer.cut_clipboard(self.clipboard, True)

    def on_paste(self, *args):
        buffer = self.book_view.get_buffer()
        buffer.paste_clipboard(self.clipboard, None, True)

    def on_copy(self, *args):
        buffer = self.book_view.get_buffer()
        buffer.copy_clipboard(self.clipboard)

    def on_delete(self, *args):
        buffer = self.book_view.get_buffer()
        buffer.delete_selection(True, True)

    def on_api_request(self, *args):
        old_key = self.config.get_value("tts", "key", str, "")

        url = yandex_tts.API_REQUEST_URL
        link_title = stat_func.get_url_host(url)

        new_key = dialogs.APIKey(self.window, old_key, url, link_title).get_key()
        if (new_key is not None) and (new_key != old_key):
            self.config.set_value("tts", "key", new_key)

    def select_folder(self):
        last_folder = self.config.get_value("task", "save_path",
                                            str, config.DEFAULT_SAVE_PATH)
        new_folder = dialogs.OpenFolder(self.window, last_folder).get_folder()
        if new_folder is not None:
            self.config.set_value("task", "save_path", new_folder)
        return new_folder

    def save_prefs(self):
        for name, val in self.tts.properties.items():
            self.config.set_("tts", name, val)
        self.config.save()
        
    def load_book(self, book_path):
        self.book = book_path
        buffer = self.book_view.get_buffer()
        lines = text_exctractor.extract_text(book_path)
        buffer.set_text(os.linesep.join(lines))

    def load_task(self, tsk_name, tsk):
        self.book = tsk_name
        buffer = self.book_view.get_buffer()

        text = []
        for tts_job in tsk.iterate_all():
            text.append(tts_job.data)

        buffer.set_text(os.linesep.join(text))



class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id = APP,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                         **kwargs)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action_about = Gio.SimpleAction.new("about", None)
        action_about.connect("activate", self.on_about)
        self.add_action(action_about)

        action_quit = Gio.SimpleAction.new("quit", None)
        action_quit.connect("activate", self.on_quit)
        self.add_action(action_quit)

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP)
        #self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down

            self.window = MainWindow(self.builder, self, self.conf)

        self.window.present()
        if self.book_path is not None:
            self.window.load_book(self.book_path)
        #Gtk.main()

    def do_command_line(self, command_line):
        arguments = command_line.get_arguments()
        options = command_line.get_options_dict()

        config_file = config.DEFAULT_CONF_FILE
        self.book_path = None

        for arg in arguments[1:]:
            if arg.startswith("--config"):
                a, *config_path = arg.split("=")
                config_file = "=".join(config_path)
            elif os.path.isfile(arg):
                self.book_path = arg



        self.conf = config.Config(config_file)
        self.conf.load()

        self.activate()
        return 0

    def on_about(self, action, param):
        dialogs.About(self.window.window).show()

    def on_quit(self, action, param):
        self.window.close()
        self.conf.save()
        print("app quit")


    def on_create(self, action, param):
        pass
    
if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)

        