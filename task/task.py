#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 26.01.17 14:17

@project: fb2
@author: pavel
"""
import os
import sys
import sqlite3

import pickle

from datetime import datetime
from collections import namedtuple


STATUS_NEW = 0
STATUS_OK = 1
STATUS_ERR = 2

Task_repr = namedtuple('Task', ['id',
                           'finished',
                           'task_name',
                           'task_params',
                           'task_save_path',
                           'created',
                           'changed'], verbose=False)

TTS_Job_repr = namedtuple('TTS_Job', ['id',
                                      'result',
                                      'fname',
                                      'data'])

sqlite3.register_converter("pickle", pickle.loads)


sqlite3.register_adapter(dict, pickle.dumps)
sqlite3.register_adapter(list, pickle.dumps)
sqlite3.register_adapter(set, pickle.dumps)



class TaskManager:
    def __init__(self, db_path):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        #new_db = not os.path.exists(db_path)

        self.connection = sqlite3.connect(self.db_path,
                                          detect_types=sqlite3.PARSE_DECLTYPES,
                                          check_same_thread=False)

        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        try:
            # Create table

            self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 finished INTEGER DEFAULT 0 ,
                                 task_name TEXT, task_params PICKLE,
                                 task_save_path TEXT,
                                 created TIMESTAMP, changed TIMESTAMP)''')
            self.connection.commit()
        except Exception as e:
            print("SQL create_table", e)

    def table_exists(self):
        try:
            params = ()
            self.cursor.execute('''SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_name = tasks  ''', params)
            return self.cursor.fetchone()[0] == 1
        except Exception as e:
            print("SQL table_exists", e)

    def create_task(self, task_name, task_params = {}, task_save_path = "./"):
        try:
            now = datetime.now()

            #task_params = pickle.dumps(task_params, pickle.DEFAULT_PROTOCOL)
            params = (task_name, task_params, task_save_path,
                      now, now)

            self.cursor.execute('''INSERT INTO tasks(
                                task_name, task_params, task_save_path,
                                created, changed) VALUES (?,?,?,?,?)''',
                                params)
            self.connection.commit()


            task_id = self.cursor.lastrowid
            task_tbl = self.task_tbl_name(task_id)
            task = Task(task_tbl, self.db_path, create=True)

            return task_id, task
        except Exception as e:
            print("SQL create_task", task_name, task_params, e)
            return None, None

    def get_task(self, task_id):
        try:
            return Task(self.task_tbl_name(task_id), self.db_path)
        except Exception as e:
            print("SQL get_task", task_id, e)

    def task_tbl_name(self, task_id):
        return "task_" + str(task_id)

    def mark_finished(self, task_id):
        try:
            now = datetime.now()
            params = (STATUS_OK, now, task_id,)
            self.cursor.execute('UPDATE tasks SET finished = ?, changed = ? WHERE id = ?', params)
            self.connection.commit()
        except Exception as e:
            print("SQL mark_finished", task_id, e)

    def mark_error(self, task_id):
        try:
            now = datetime.now()
            params = (STATUS_ERR, now, task_id,)
            self.cursor.execute('UPDATE tasks SET finished = ?, changed = ? WHERE id = ?', params)
            self.connection.commit()
        except Exception as e:
            print("mark_error", task_id, e)

    def delete(self, task_id):
        if task_id != "tasks":
            try:
                self.cursor.execute('DROP TABLE ' + self.task_tbl_name(task_id))
                self.cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                self.connection.commit()
            except Exception as e:
                print("SQL delete", task_id, e)

    def update(self, task_id, new_name = None, new_params = None, new_path = None):
        try:
            now = datetime.now()
            if new_name is not None:
                self.cursor.execute('UPDATE tasks SET task_name = ? WHERE id = ?', (new_name, task_id))
            if new_params is not None:
                self.cursor.execute('UPDATE tasks SET task_params = ? WHERE id = ?', (new_params, task_id))
            if new_path is not None:
                self.cursor.execute('UPDATE tasks SET task_save_path = ? WHERE id = ?', (new_path, task_id))

            self.cursor.execute('UPDATE tasks SET changed = ? WHERE id = ?', (now, task_id))

            self.connection.commit()
        except Exception as e:
            print("SQL update", task_id, new_name, new_params, e)

    def iterate_tasks(self):
        try:
            for row in self.cursor.execute('SELECT * FROM tasks ORDER BY id'):
                yield Task_repr._make(row)
        except Exception as e:
            print("SQL iterate_tasks", e)

    def get_task_repr(self, task_id):
        try:
            self.cursor.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
            return Task_repr._make(self.cursor.fetchone())
        except Exception as e:
            print("SQL get_task_repr", task_id, e)


    def close(self):
        # Save (commit) the changes
        self.connection.commit()

        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        self.connection.close()



class Task:
    def __init__(self, tbl, db_path, create = False):
        db_path = os.path.expanduser(db_path)
        self.tbl = str(tbl)

        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        if create: self.create_db()

    def create_db(self):
        # Create table
        try:
            params = ()
            sql = '''CREATE TABLE {tbl}
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         result INTEGER DEFAULT 0,
                         fname TEXT, data TEXT)'''.format(tbl = self.tbl)
            self.cursor.execute(sql, params)
            self.connection.commit()
        except Exception as e:
            print("SQL create_db", e)

    def add_line(self, fname, data, commit = True):
        try:
            params = (fname, data)
            sql = 'INSERT INTO {tbl}(fname, data) VALUES (?,?)'.format(tbl = self.tbl)
            self.cursor.execute(sql, params)
            if commit:
                self.connection.commit()
        except Exception as e:
            print("SQL add_line", fname, data, e)

    def iterate_all(self):
        try:
            params = ()
            sql = 'SELECT * FROM {tbl} ORDER BY id'.format(tbl = self.tbl)
            for row in self.cursor.execute(sql, params):
                yield TTS_Job_repr._make(row)
        except Exception as e:
            print("SQL iterate_all", e)

    def iterate_incompleted(self):
        try:
            params = (STATUS_NEW,)
            sql = 'SELECT * FROM {tbl} WHERE result=? ORDER BY id'.format(tbl = self.tbl)
            for row in self.cursor.execute(sql, params):
                yield TTS_Job_repr._make(row)
        except Exception as e:
            print("SQL iterate_incompleted", e)

    def mark_completed(self, segment_id, result, commit = True):
        try:
            params = (result, segment_id,)
            sql = 'UPDATE {tbl} SET result = ? WHERE id=?'.format(tbl = self.tbl)
            self.cursor.execute(sql, params)
            if commit:
                self.connection.commit()
        except Exception as e:
            print("SQL mark_completed", e)

    def num_total(self):
        try:
            params = ()
            sql = 'SELECT count(id) FROM {tbl}'.format(tbl = self.tbl)
            self.cursor.execute(sql, params)
            return self.cursor.fetchone()[0]
        except Exception as e:
            print("SQL num_total", e)

    def num_completed(self):
        try:
            params = (STATUS_OK, )
            sql = 'SELECT count(id) FROM {tbl} WHERE result=?'.format(tbl = self.tbl)
            self.cursor.execute(sql, params)
            return self.cursor.fetchone()[0]
        except Exception as e:
            print("SQL num_completed", e)

    def num_errors(self):
        try:
            params = (STATUS_ERR, )
            sql = 'SELECT count(id) FROM {tbl} WHERE result=?'.format(tbl=self.tbl)
            self.cursor.execute(sql, params)
            return self.cursor.fetchone()[0]
        except Exception as e:
            print("SQL num_errors", e)

    def commit(self):
        self.connection.commit()

    def close(self):
        # Save (commit) the changes
        self.connection.commit()

        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        self.connection.close()


def main(*argv):
    import config
    tm = TaskManager(config.DEFAULT_TASK_FILE)

    #tm.delete_all()
    for row in tm.iterate_tasks():
        print(row)

    tm.close()


if __name__ == "__main__":
    main(sys.argv)

