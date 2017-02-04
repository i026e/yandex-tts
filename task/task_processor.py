#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 31.01.17 10:03

@project: fb2
@author: pavel
"""

import os
import time
from multiprocessing.dummy import Pool as ThreadPool
from threading import Lock

import task
from tts import yandex_tts


class TTS_Processor:
    def __init__(self, num_threads = 5,
                 on_progress_cb = print,
                 on_error_cb = print,
                 on_complete_cb = print):
        self.num_threads = num_threads
        self.thread_pool = None

        self.on_progress_cb = on_progress_cb
        self.on_error_cb = on_error_cb
        self.on_complete_cb = on_complete_cb
        self.on_progress_lock = Lock()
        self.on_error_lock = Lock()
        self.on_complete_lock = Lock()

    def cancel(self):
        self.cancelled = True

    def download(self, id_, name, tts_task, save_path, task_params):
        self.cancelled = False

        self.task_id = id_
        self.tts_task = tts_task

        self.num_total = self.tts_task.num_total()
        self.num_completed = self.tts_task.num_completed()
        self.num_errors = self.tts_task.num_errors()

        self.set_save_dir(save_path, name, id_)
        self.tts_params = task_params.get("tts",  {})


        self.bytes_downloaded = 0
        self.start_time = time.monotonic()

        self.thread_pool = ThreadPool(self.num_threads)
        #results = self.thread_pool.map(self._background_load, self.tts_task.iterate_incompleted())
        fragments = [f for f in self.tts_task.iterate_incompleted()]
        results = self.thread_pool.map(self._background_load, fragments)

        for (frag_id, res_ok) in results:
            if frag_id is not None:
                status = task.STATUS_OK if res_ok else task.STATUS_ERR
                self.tts_task.mark_completed(frag_id, status, commit=False)

        self.tts_task.commit()
        return self.num_total, self.num_completed, self.num_errors

    def _background_load(self, tts_job_repr):
        if self.cancelled:
            return None, False

        voice = yandex_tts.Voice.new(self.tts_params)

        frag_id = tts_job_repr.id
        fname = tts_job_repr.fname
        fpath = os.path.join(self.save_dir, fname)

        result_path = voice.save_audio(tts_job_repr.data, fpath,
                                       on_progress=self.on_fragment_progress,
                                       on_result=self.on_fragment_complete,
                                       on_error=self.on_fragment_error)

        return (frag_id, result_path is not None)


    def set_save_dir(self, save_path, task_name, task_id):
        save_dir = os.path.join(save_path, str(task_name) + "_" + str(task_id))
        os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir

    def on_fragment_complete(self, path):
        print("complete", path)
        with self.on_complete_lock:
            if path is not None:
                self.num_completed += 1
            else:
                self.num_errors += 1

            self.on_complete_cb(self.task_id, self.num_total, self.num_completed, self.num_errors)

    def on_fragment_progress(self, chunk, chunk_size, total_size):
        print(chunk, chunk_size, total_size)
        with self.on_progress_lock:
            self.bytes_downloaded += chunk_size
            time_delta = time.monotonic() - self.start_time
            self.on_progress_cb(self.task_id, self.bytes_downloaded, time_delta)

    def on_fragment_error(self, err):
        print(err)
        with self.on_error_lock:
            self.on_error_cb(self.task_id, err)

if __name__ == "__main__":
    task_mgr = task.TaskManager()
    proc = TTS_Processor()

    for t in task_mgr.iterate_tasks():
        if t.finished != task.STATUS_OK:
            print(t.task_name)

            tts_task = task_mgr.get_task(t.id)
            tot, comp, err = proc.download(t.id, tts_task, t.task_params)
            tts_task.close()


            if tot == comp:
                task_mgr.mark_finished(t.id)
            elif err > 0:
                task_mgr.mark_error(t.id)


