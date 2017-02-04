#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 14:57:11 2017

@author: pavel
"""
import os
import sys
import xml.etree.ElementTree as ET

def strip_namespace(tag):
    return tag.split("}")[-1]

def extract_text_plain(text_file):
    text = []
    with open(text_file, "r") as f:
        for line in f:
            text.append(line.strip())
    return text

def extract_text_xml(xml_file, ignore_tags = {}):
    text = []

    def recursion(subtree):
        if subtree.text is not None:
            text.append(subtree.text.strip())
        for child in subtree:
            if strip_namespace(child.tag) not in ignore_tags:
                recursion(child)


    tree = ET.parse(xml_file)
    recursion(tree.getroot())
    return text

def exctract_text_fb2(fb2_file):
    return extract_text_xml(fb2_file, {"description", "id", "style", "a", "image", "binary"})


def extract_text(file_path):
    file_path = os.path.expanduser(file_path)
    filename, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    try:
        if file_extension in {".fb2"}:
            return exctract_text_fb2(file_path)
        elif file_extension in {".xml", ".html", ".htm"}:
            return extract_text_xml(file_path)
        else:
            return extract_text_plain(file_path)
    except Exception as e:
        print(e)
        return []


def main(pathes):
    for path in pathes:
        txt = extract_text(path)
        for line in txt:
            print(line)
    
if __name__ == "__main__":
    main(sys.argv[1:])

