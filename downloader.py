#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 30.01.17 17:20

@project: fb2
@author: pavel
"""
import os
import signal
import sys

signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject, Gdk, Gio

APP = "org.text-to-audio"
DIR = os.path.dirname(os.path.realpath(__file__))
GLADE_FILE = "ui/downloader.glade"

import locale
locale.setlocale(locale.LC_ALL, '')
if os.path.isdir("../locale"):
    locale.bindtextdomain(APP, "../locale")
    locale.textdomain(APP)

from threading import Thread

import creator
from ui import dialogs
import config
from task import task, task_processor
import stat_func


class TextColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, tooltip_text, model_index_txt,
                 *args, **kwargs):
        super(TextColumn, self).__init__(*args, **kwargs)

        self.title = Gtk.Label(column_name)
        self.title.set_tooltip_text(tooltip_text)
        self.title.show()
        self.set_widget(self.title)

        renderer_text = Gtk.CellRendererText()
        self.cell_renderers = (renderer_text,)

        self.pack_start(renderer_text, expand=True)
        self.add_attribute(renderer_text, "text", model_index_txt)

        self.set_resizable(True)
        self.set_sort_column_id(model_index_txt)

    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)

class FlagColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, tooltip_text, model_index_bool,
                 on_toggle, *args, on_toggle_data=None, **kwargs):
        super(FlagColumn, self).__init__(*args, **kwargs)

        self.title = Gtk.Label(column_name)
        self.title.set_tooltip_text(tooltip_text)
        self.title.show()
        self.set_widget(self.title)

        renderer_flag = Gtk.CellRendererToggle()
        self.cell_renderers = (renderer_flag,)

        renderer_flag.connect("toggled", on_toggle, on_toggle_data)

        self.pack_start(renderer_flag, expand=False)
        self.add_attribute(renderer_flag, "active", model_index_bool)

        self.set_clickable(True)
        self.set_resizable(False)

        # self.set_sort_indicator(True)

    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)

class ImageTextColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, tooltip_text,
                 model_index_txt,  model_index_img,
                 *args, **kwargs):
        super(ImageTextColumn, self).__init__(*args, **kwargs)

        self.title = Gtk.Label(column_name)
        self.title.set_tooltip_text(tooltip_text)
        self.title.show()
        self.set_widget(self.title)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_text = Gtk.CellRendererText()
        self.cell_renderers = (renderer_pixbuf, renderer_text, )

        self.pack_start(renderer_pixbuf, expand = False)
        self.add_attribute(renderer_pixbuf, "icon-name", model_index_img)

        self.pack_start(renderer_text, expand = True)
        self.add_attribute(renderer_text, "text", model_index_txt)

        self.set_resizable(True)
        self.set_sort_column_id(model_index_txt)

    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)




class TaskModel:
    COL_TASK_ID             = 0
    COL_TASK_NAME           = 1
    COL_TASK_PARAMS         = 2

    COL_TASK_STATUS_IMG     = 3
    COL_TASK_STATUS_ACTIVE  = 4
    COL_TASK_STATUS_NEW     = 5
    COL_TASK_STATUS_OK      = 6
    COL_TASK_STATUS_ERR     = 7

    COL_TASK_PROGRESS       = 8
    COL_TASK_SPEED          = 9

    COL_TASK_CREATED        = 10
    COL_TASK_CHANGED        = 11
    COL_TASK_PATH           = 12


    COLUMN_TYPES = [int, str, object,
                    str, bool, bool, bool, bool,
                    str, str,
                    str, str, str]

    def __init__(self, builder, task_mgr):
        self.list_store = Gtk.ListStore(*self.COLUMN_TYPES)
        self.task_mgr = task_mgr

        self.load_tasks()
        self.iters_cache = {}
        self.procs = {}

    def get_model(self):
        return self.list_store

    def load_tasks(self):
        self.list_store.clear()
        for task_repr in self.task_mgr.iterate_tasks():
            self.add_task(task_repr)

    def get_image(self, active = False, new = False, ok = False, err = False):
        if active:
            return "gtk-media-play"
        if err:
            return "gtk-dialog-error"
        if ok:
            return "gtk-yes"
        if new:
            return None

    def get_iter(self, task_id):
        if task_id in self.iters_cache:
            return self.iters_cache[task_id]

        result_iter = None

        iter = self.list_store.get_iter_first()
        while iter is not None:
            if self.list_store.get_value(iter, self.COL_TASK_ID) == task_id:
                result_iter = iter
                break
            iter = self.list_store.iter_next(iter)

        if result_iter is not None:
            self.iters_cache[task_id] = result_iter

        return result_iter

    def get_task_id(self, iter):
        return self.list_store.get_value(iter, self.COL_TASK_ID)

    def get_name(self, iter):
        return self.list_store.get_value(iter, self.COL_TASK_NAME)

    def get_save_path(self, iter):
        return self.list_store.get_value(iter, self.COL_TASK_PATH)

    def task_columns(self, task_repr, active = False):
        id_ = task_repr.id
        name = task_repr.task_name
        params = task_repr.task_params
        save_path = task_repr.task_save_path

        new = (task_repr.finished == task.STATUS_NEW)
        ok = (task_repr.finished == task.STATUS_OK)
        err = (task_repr.finished == task.STATUS_ERR)

        img = self.get_image(active, new, ok, err)

        created = stat_func.get_date(task_repr.created)
        changed = stat_func.get_date(task_repr.changed)


        progress = "--"
        speed = "--"

        return [id_, name, params,
                img, active, new, ok, err,
                progress, speed,
                created, changed, save_path]


    def add_task(self, task_repr):
        def append(args):
            self.list_store.append(args)
            return False  # for idle_add

        GObject.idle_add(append, self.task_columns(task_repr))

    def start(self, iter):
        active = self.list_store.get_value(iter, self.COL_TASK_STATUS_ACTIVE)
        completed = self.list_store.get_value(iter, self.COL_TASK_STATUS_OK)
        if (not active) and (not completed):
            thr = Thread(target=self.start_task_backround, args=(iter,))
            thr.start()

    def stop(self, iter):
        task_id = self.get_task_id(iter)
        if task_id in self.procs:
            self.procs[task_id].cancel()

    def delete(self, iter):
        task_id = self.get_task_id(iter)
        if task_id in self.procs:
            self.procs[task_id].cancel()
        self.task_mgr.delete(task_id)
        self.list_store.remove(iter)

    def update(self, task_id):
        iter = self.get_iter(task_id)
        if iter is not None:
            new_task_repr = self.task_mgr.get_task_repr(task_id)
            for (ind, val) in enumerate(self.task_columns(new_task_repr)):
                GObject.idle_add(self.list_store.set_value, iter, ind, val)

    def replace(self, task_id, new_task_id):
        iter = self.get_iter(task_id)
        if iter is not None:
            if task_id in self.procs:
                self.procs[task_id].cancel()
            self.task_mgr.delete(task_id)

            new_task_repr = self.task_mgr.get_task_repr(new_task_id)
            for (ind, val) in enumerate(self.task_columns(new_task_repr)):
                GObject.idle_add(self.list_store.set_value, iter, ind, val)

    def start_task_backround(self, iter):
        task_id = self.get_task_id(iter)
        job = self.task_mgr.get_task(task_id)
        if job is not None:

            img = self.get_image(active=True)
            GObject.idle_add(self.list_store.set_value, iter, self.COL_TASK_STATUS_ACTIVE, True)
            GObject.idle_add(self.list_store.set_value, iter, self.COL_TASK_STATUS_IMG, img)


            processor = task_processor.TTS_Processor(on_progress_cb=self.on_fragment_process,
                                                     on_complete_cb=self.on_fragment_complete,
                                                     on_error_cb=self.on_fragment_error)
            self.procs[task_id] = processor
            job_params = self.list_store.get_value(iter, self.COL_TASK_PARAMS)

            task_name = self.get_name(iter)
            task_save_path = self.get_save_path(iter)

            result = processor.download(task_id, task_name, job, task_save_path, job_params)
            num_total, num_completed, num_errors = result

            job.close()
            self.procs.pop(task_id)

            if num_total == num_completed:
                self.task_mgr.mark_finished(task_id)
            elif num_errors > 0:
                self.task_mgr.mark_error(task_id)

            self.update(task_id)


    def on_fragment_complete(self, task_id, num_total, num_completed, num_errors):
        iter = self.get_iter(task_id)
        if iter is not None:
            val = stat_func.progress(num_total, num_completed, num_errors)
            GObject.idle_add(self.list_store.set_value, iter, self.COL_TASK_PROGRESS, val)

    def on_fragment_process(self, task_id, bytes_downloaded, time_delta):
        iter = self.get_iter(task_id)
        if iter is not None:
            speed = stat_func.speed(bytes_downloaded, time_delta)
            GObject.idle_add(self.list_store.set_value, iter, self.COL_TASK_SPEED, speed)

    def on_fragment_error(self, task_id, error):
        iter = self.get_iter(task_id)


class TaskView:
    def __init__(self, builder, task_model):
        #self.builder = builder
        self.view = builder.get_object("tasks_view")
        self.model = task_model
        self.context_menu = builder.get_object("context_menu")

        self.view.set_model(self.model.get_model())

        # callbacks
        self.view.connect("button-press-event", self.on_mouse_clicked)
        self.view.connect("key-press-event", self.on_key_pressed)

        # allow multiple selection
        self.tree_selection = self.view.get_selection()
        self.tree_selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.__add_columns__()

    def __add_columns__(self):

        name_column = ImageTextColumn("Name", "Name",
                                 self.model.COL_TASK_NAME,
                                 self.model.COL_TASK_STATUS_IMG)
        self.view.append_column(name_column)

        progress_column = TextColumn("Progress", "Progress",
                                 self.model.COL_TASK_PROGRESS)
        self.view.append_column(progress_column)

        speed_column = TextColumn("Speed", "Speed",
                                     self.model.COL_TASK_SPEED)
        self.view.append_column(speed_column)

        created_column = TextColumn("Created", "Created",
                                     self.model.COL_TASK_CREATED)
        self.view.append_column(created_column)

        changed_column = TextColumn("Modified", "Modified",
                                     self.model.COL_TASK_CHANGED)
        self.view.append_column(changed_column)

        path_column = TextColumn("Path", "Path",
                                    self.model.COL_TASK_PATH)
        self.view.append_column(path_column)

    def on_mouse_clicked(self, widget, event):
        if event.button == 3: #right button
            self.show_context_menu(widget, event)
            return True
        if event.type == Gdk.EventType._2BUTTON_PRESS: #double click
            self.on_double_click(widget, event)
            return True

    def on_key_pressed(self, widget, event):
        #do not reset selection
        keyname = Gdk.keyval_name(event.keyval)
        print(keyname, "button pressed")

        if keyname in {}:
            #execute
            #self.keyboard_keys_actions.get(keyname, print)(widget, event)
            return True

    def on_double_click(self, widget, event):
        pass

    def show_context_menu(self, widget, event):
        self.context_menu.popup( None, None, None, None, 0, event.time)

    def iterate_selected(self):
        (model, pathlist) = self.tree_selection.get_selected_rows()

        for path in pathlist :
            tree_iter = model.get_iter(path)
            yield model, tree_iter


class MainWindow:
    def __init__(self, builder, app, conf):

        self.builder = builder
        self.builder.add_from_file(GLADE_FILE)
        self.app = app
        self.config = conf

        self.window = self.builder.get_object("main_window")
        self.window.set_application(app)
        self.window.connect("delete-event", app.on_quit)

        self.task_mgr = task.TaskManager(self.config.get_value("app", "db_path",
                                                               str, config.DEFAULT_TASK_DB_FILE))
        self.task_model = TaskModel(self.builder, self.task_mgr)
        self.task_view = TaskView(self.builder, self.task_model)

        self.init_actions()

    def present(self):
        self.window.present()
        #Gtk.main()

    def init_actions(self):
        action_start = Gio.SimpleAction.new("start", None)
        action_start.connect("activate", self.on_start)
        self.window.add_action(action_start)

        action_stop = Gio.SimpleAction.new("stop", None)
        action_stop.connect("activate", self.on_stop)
        self.window.add_action(action_stop)

        action_del = Gio.SimpleAction.new("delete", None)
        action_del.connect("activate", self.on_delete)
        self.window.add_action(action_del)

        action_edit = Gio.SimpleAction.new("edit", None)
        action_edit.connect("activate", self.on_edit)
        self.window.add_action(action_edit)

        action_create = Gio.SimpleAction.new("create", None)
        action_create.connect("activate", self.on_create)
        self.window.add_action(action_create)


    def close(self, *args):
        #self.save_prefs()
        print("closing")
        self.task_mgr.close()

    def on_delete(self, *args):
        to_delete = [iter for (model, iter) in self.task_view.iterate_selected()]
        names_list = [self.task_model.get_name(iter) for iter in to_delete]
        message = "Delete following tasks: \r\n{names} ?".format(names = os.linesep.join(names_list))
        if dialogs.Confirmation(self.window, message).ok():
            for iter in to_delete:
                self.task_model.delete(iter)

    def on_start(self, *args):
        for (model, iter) in self.task_view.iterate_selected():
            self.task_model.start(iter)

    def on_stop(self, *args):
        for (model, iter) in self.task_view.iterate_selected():
            self.task_model.stop(iter)

    def on_create(self, *args):
        def on_new_task(task_id):
            task_repr = self.task_mgr.get_task_repr(task_id)
            if task_repr is not None:
                self.task_model.add_task(task_repr)

        creator_window = creator.MainWindow(self.builder, self.app, self.config,
                                            parent_window=self.window,
                                            report_cb=on_new_task,
                                            close_on_add=True)
        creator_window.present()

    def on_edit(self, *args):

        for (model, iter) in self.task_view.iterate_selected():
            tsk_id = self.task_model.get_task_id(iter)
            on_new_task = lambda new_task_id, old_tsk_id = tsk_id: self.task_model.replace(old_tsk_id, new_task_id)

            tsk = self.task_mgr.get_task(tsk_id)
            tsk_repr = self.task_mgr.get_task_repr(tsk_id)

            tsk_name = tsk_repr.task_name
            tsk_path = tsk_repr.task_save_path
            tsk_tts = tsk_repr.task_params.get("tts")

            conf_copy = self.config.copy()
            conf_copy.set_group("tsk", tsk_tts)
            conf_copy.set_value("task", "save_path", tsk_path)

            creator_window = creator.MainWindow(self.builder, self.app, conf_copy,
                                            parent_window=self.window,
                                            report_cb=on_new_task,
                                            close_on_add=True)
            creator_window.load_task(tsk_name, tsk)
            creator_window.present()



class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id = APP,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                         **kwargs)
        self.window = None

#        self.add_main_option("test", ord("t"), GLib.OptionFlags.NONE,
#                             GLib.OptionArg.NONE, "Command line test", None)


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
        #Gtk.main()

    def do_command_line(self, command_line):
        arguments = command_line.get_arguments()

        config_file = config.DEFAULT_CONF_FILE

        for arg in arguments[1:]:
            if arg.startswith("--config"):
                a, *config_path = arg.split("=")
                config_file = "=".join(config_path)

        self.conf = config.Config(config_file)
        self.conf.load()
        self.activate()
        return 0

    def on_about(self, *args):
        dialogs.About(self.window.window).show()

    def on_quit(self, *args):
        print("app quit")
        self.conf.save()

        if dialogs.Confirmation(self.window.window, "Quit").ok():
            self.window.close()
            self.quit()

    def on_new_task(self, task_ids):
        print(task_ids)


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)



