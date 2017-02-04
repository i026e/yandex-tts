#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 02.02.17 14:32

@project: fb2
@author: pavel
"""
from urllib.parse import urlparse
from datetime import datetime
from math import log

SIZE_NAMES = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]

def get_date(timestamp):
    if type(timestamp) != datetime:
        timestamp = datetime.fromtimestamp(timestamp)
    return str(timestamp.isoformat(sep = " ", timespec="seconds"))

def scale_step(min_val, max_val, num_steps = 100):
    range_ = abs(max_val - min_val)
    range_order = round(log(range_, 10))
    step_order = round(log(num_steps, 10))
    return 10 ** (range_order - step_order)

def progress(num_total, num_completed, num_errors):
    return "{got} of {tot} ({err} errors)".format(got = num_completed + num_errors,
                                                  tot = num_total,
                                                  err = num_errors)

def speed(bytes, timedelta):
    val = bytes / timedelta

    unit_index = 0

    while (val > 1024) and unit_index < (len(SIZE_NAMES) - 1):
        val /= 1024
        unit_index += 1

    return "{val:.2f} {unit}/s".format(val = val, unit = SIZE_NAMES[unit_index] )

def get_url_host(url):
    p = urlparse(str(url))
    return p.scheme + "://"  + p.netloc
