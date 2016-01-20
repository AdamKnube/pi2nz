#!/usr/bin/env python3
#

import os

_debug_level = 3
_music_folder = '/mnt/store/Media/Audio/Music'

def dprint(data='', level=0):
    if (level > _debug_level): return
    if (data == ''): return
    print('[' + str(level) + ']  ' + data)
    
def getMusic(where=''):
    templist = []
    dprint('Testing: ' + _music_folder, 1)
    for root, folders, files in os.walk(where):
        for thisfile in files:
            absolute = os.path.join(root, thisfile)    
            if ( thisfile[-3:].lower() == 'mp3'):
                templist.append(absolute)
                dprint('Added: ' + thisfile, 1)
            else: dprint('Ignored: ' + thisfile + ' (' + thisfile[-3:].lower() + ')', 1)
    return templist

def runmain():
    thelist = getMusic(_music_folder)
    for item in thelist:
        print(item)
    return 0

if (__name__ == '__main__'):
    exit(runmain())
    