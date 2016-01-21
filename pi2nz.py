#!/usr/bin/env python3
#

import os
import threading
import http.server

_debug_level = 5
_bind_address = ('', 8080)
_music_folder = '/mnt/store/Media/Audio/Music'

# Debug printer
def dprint(data='', level=0):
    if (level > _debug_level): return
    if (data == ''): return
    print('[' + str(level) + ']  ' + data)

# Music player
class tunez_machine(threading.Thread):
    def __init__(self):
        dprint("Music thread initializing", 1)
    def run(self):
        dprint("Music thread running", 1)

# Webserver backend
class serv_backend(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        dprint("HEAD", 1)
        
    def do_GET(self):
        dprint("GET", 1)
        
    def go_POST(self):
        dprint("POST", 1)        

# Make an array of mp3 files    
def getMusic(where=''):
    templist = []
    dprint('Testing: ' + _music_folder, 1)
    for root, folders, files in os.walk(where):
        for thisfile in files:
            absolute = os.path.join(root, thisfile)    
            if ( thisfile[-3:].lower() == 'mp3'):
                templist.append(absolute)
                dprint('Added: ' + thisfile, 2)
            else: dprint('Ignored: ' + thisfile + ' (' + thisfile[-3:].lower() + ')', 2)
    return templist

def runmain():
    thelist = getMusic(_music_folder)
    theserver = http.server.HTTPServer(_bind_address, serv_backend)
    theserver.serve_forever()    
    return 0




if (__name__ == '__main__'):
    exit(runmain())
    