#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 30.01.17 15:27

@project: fb2
@author: pavel
"""
import os
import sys

class Splitter:
    def __init__(self, max_size):
        #max size in bytes
        assert max_size > 1
        self.max_size = max_size

        self.buffer = []
        self.buffer_size = 0

    def get_size_bytes(self, text):
        return len(text.encode('utf-8'))

    def split(self, text):
        for line in text.split(os.linesep):
            size = self.get_size_bytes(line)
            if size + self.buffer_size < self.max_size:
                self._append(line, size)
            else:

                if size <= self.max_size:
                    yield self._flush()
                    self._append(line, size)
                else:
                    for word in self.split_by_space(line):
                        yield(word)
        yield self._flush()

    def split_by_space(self, line):
        for word in line.split(" "):
            size = self.get_size_bytes(word)
            if size + self.buffer_size  <= self.max_size:
                self._append(word, size)
            else:

                if size <= self.max_size:
                    yield self._flush()
                    self._append(word, size)

                else:
                    for fragment in self.split_word(word):
                        yield fragment


    def split_word(self, word):
        fragment_size = 0
        start_index = 0

        for ind, letter in enumerate(word):
            letter_size = self.get_size_bytes(letter)
            if fragment_size + letter_size <= self.max_size:
                fragment_size += letter_size
            else:
                yield word[start_index: ind]

                start_index = ind
                fragment_size = letter_size

        if fragment_size > 0:
            yield word[start_index:]

    def _append(self, subtext, size):
        self.buffer.append(subtext)
        self.buffer_size += size

    def _flush(self):
        text = " ".join(self.buffer)
        self.buffer = []
        self.buffer_size = 0
        return text

if __name__ == "__main__":
    text = """Год выпуска: 2017 Жанр: Рисованная анимация, Приключения, Комедия Продолжительность: ~00:22:00 х Серия  Описание: Пора Приключений - американский анимационный сериал, созданный Пендлтоном Вордом. Сериал повествует о необыкновенных и весёлых приключениях двух лучших друзей: мальчика Финна и его собаки Джейка. Действие сериала происходит в волшебной стране Ууу. Финн - 13-летний мальчик, который обожает путешествовать и спасать принцесс из лап ужасных монстров и злодеев, населяющих Землю Ууу. Джейк - лучший друг Финна. Это волшебная собака со способностью растягивать своё тело до практически любых размеров и форм. Джейку 28 лет и он исполняет роль эдакого приятеля-наставника Финна, а его волшебные способности помогают мальчику в его борьбе со злом.  Доп. информация: Cезон выходит с января 2016. Видео взято с iTunes.  Язык: Английский Перевод: Субтитры Автор перевода: Павел Самойлов aka Tanis  Качество видео: WEB-DL Формат видео: MKV Размер кадра: 1280 x 720 Видео: MPEG-4 AVC/H.264 23.976fps 2500-3500 kb/s Аудио: AAC 48000Hz 2ch ~192 kb/s VBR  ---  ВНИМАНИЕ! Если вам понравился перевод и вы хотите поблагодарить переводчика материально, вот кошельки для донатов: WMR: R969226566530 WMZ: Z173401952013 Я.Д: 410011552426170 MasterCard: 5189 0100 0449 8532 Павел Самойлов."""
    #text = "abracadabra"


    spl = Splitter(1500)
    ind = 0
    for fragment in spl.split(text):
        print(ind, len(fragment), fragment)
