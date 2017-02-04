#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 19:11:11 2017

@author: pavel
"""

import os
import urllib
import urllib.parse
import urllib.request

API_REQUEST_URL = "https://tech.yandex.com/speechkit/cloud/doc/dg/concepts/speechkit-dg-tts-docpage/"

URL = "https://tts.voicetech.yandex.net/generate"
MAX_SYMBOLS = 1500

PROPERTIES = {"lang": (list, ["ru-RU", "en-US", "tr-TR", "uk-UK"]),
              "speaker": (list, ["jane", "omazh", "zahar", "ermil", "oksana", "alyss"]),
              "format": (list, ["mp3", "wav", "opus"]),
              "emotion": (list, ["", "good", "evil", "neutral"]),
              "speed": (range, (0.1, 3.0))
              }

PROPERTIES_TYPES = {"lang": str,
                    "speaker": str,
                    "format": str,
                    "emotion": str,
                    "speed": float,
                    "key": str
                    }

DEFAULT_PROPERTIES = {"lang": "ru-RU",
                      "speaker": "jane",
                      "format": "mp3",
                      "key": "6d836308-8e05-400e-99cc-d21c8d54139e",
                      "speed": 0.1,
                      }

PROPERTIES_LBLS = {"lang": "Language",
                   "speaker": "Speaker",
                   "format": "Format",
                   "emotion": "Emotion",
                   "speed": "Speed",
                   "key": "Key"
                   }


class Voice:
    def __init__(self, key = ""):
        self.properties = DEFAULT_PROPERTIES.copy()
        self.properties["key"] = key

    @staticmethod
    def new(properties):
        v = Voice()
        v.properties = properties
        return v

    def set_key(self, new_key):
        self.properties["key"] = new_key

    def get_key(self):
        return self.properties["key"]

    def set_value(self, property_name, val):
        if property_name in PROPERTIES:
            self.properties[property_name] = PROPERTIES_TYPES[property_name](val)

    def get_value(self, property_name):
        return self.properties.get(property_name)


    def save_audio(self, text, fpath,
                   on_progress = print,
                   on_result = print,
                   on_error = print):
        subtext = text[:MAX_SYMBOLS] # cut

        result_path = None

        request_params = self._build_request_params(subtext)
        request_params = urllib.parse.urlencode(request_params).encode('ascii')
        try:
            result_path, headers = urllib.request.urlretrieve(url=URL,
                                                          filename=fpath,
                                                          reporthook=on_progress,
                                                          data=request_params)
        except Exception as e:
            on_error(e)
        finally:
            on_result(result_path)
            return result_path


    def _build_request_params(self, text):
        request_params = {"text":str(text)}

        for name, val in self.properties.items():
            if val is not None:
                val = str(val)
                if len(val) > 0:
                    request_params[name] = val

        return request_params
        
        
if __name__ == "__main__":
    text = "1 2 3 4 5 6 7 8 9 10"
    v = Voice()
    v.save_audio(text, "./123.mp3")
    