#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 08:53:57 2017

@author: pavel
"""
import os
import json

DEFAULT_CONF_FILE       = "~/.config/yandex-tts/conf.json"
DEFAULT_TASK_DB_FILE    = "~/.config/yandex-tts/tasks.db"
DEFAULT_SAVE_PATH       = "~/Downloads"

class Config:
    def __init__(self, conf_file):
        self.conf_file = os.path.expanduser(conf_file)
        self.parameters = {}
        
    def load(self):
        try:
            with open(self.conf_file, "r") as f:
                data = f.read()
                js_data = json.loads(data)

                if type(js_data) != dict:
                    raise TypeError("Invalid config data type {t}".format(t = str(type(js_data))))

                self.parameters = js_data

        except Exception as e:
            print("problem while reading file", self.conf_file, ":", e)
            
    def save(self):
        try:
            directory = os.path.dirname(self.conf_file)
            os.makedirs(directory , exist_ok=True)

            with open(self.conf_file, "w") as f:
                data = json.dumps(self.parameters, sort_keys=True, indent=4)
                f.write(data)
        except Exception as e:
            print("problem while writing file", self.conf_file, e)
            
    def copy(self):
        conf = Config(self.conf_file)
        conf.parameters = self.parameters.copy()
        return conf

    def get_value(self, group, name, val_type, default_val):
        if group not in self.parameters:
            self.parameters[group] = {}

        new_val = default_val

        if name not in self.parameters[group]:
            self.parameters[group][name] = default_val
        else:
            tmp_val = self.parameters[group][name]
            try:
                new_val = val_type(tmp_val)
                self.parameters[group][name] = new_val
            except Exception as e:
                self.parameters[group][name] = default_val
                print("problem to convert", tmp_val, "to", str(val_type))
                print(e)

        return new_val

        
    def set_value(self, group, name, value):
        if group not in self.parameters:
            self.parameters[group] = {}
        self.parameters[group][name] = value

    def get_group(self, group):
        if group not in self.parameters:
            self.parameters[group] = {}
        return self.parameters[group]

    def set_group(self, group, gr_dict):
        if type(gr_dict) == dict:
            self.parameters[group] = gr_dict
        else:
            raise TypeError("Invalid group data type {t}".format(t=str(type(gr_dict))))
        