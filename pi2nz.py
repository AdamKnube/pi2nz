#!/usr/bin/env python3
#

#==============================================================================#
_debug_level_ = 3                                   # higher = spammier
_bind_address_ = ('', 8080)                         # bind address/port
_music_folder_ = '/mnt/store/Media/Audio/Music'     # mp3 music folder
#==============================================================================#

import os
import threading
import http.server

_DINFO_ = 1
_DSPAM_ = 2
_DTEST_ = 3

# Debug printer
def dprint(data='', dlevel=0):
    if (dlevel > _debug_level_): return
    if (data == ''): return
    print('[' + str(dlevel) + ']  ' + data)

# Music player
class tunez_machine(threading.Thread):
    def __init__(self):
        dprint("Music thread initializing", _DSPAM_)
    
    def run(self):
        dprint("Music thread running", _DINFO_)

# Webserver backend
class serv_backend(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        dprint(self.requestline, _DINFO_)
        
    def do_GET(self):
        dprint(self.requestline, _DINFO_)
        
    def go_POST(self):
        dprint(self.requestline, _DINFO_)        

# Make an array of mp3 files    
def getMusic(where=''):
    templist = []
    dprint('Testing: ' + _music_folder, _DINFO_)
    for root, folders, files in os.walk(where):
        for thisfile in files:
            absolute = os.path.join(root, thisfile)    
            if ( thisfile[-4:].lower() == '.mp3'):
                templist.append(absolute)
                dprint('Added: ' + thisfile, _DSPAM_)
            else: dprint('Ignored: ' + thisfile + ' (' + thisfile[-4:].lower() + ')', _DSPAM_)
    return templist

def runmain():
    thelist = getMusic(_music_folder_)
    theserver = http.server.HTTPServer(_bind_address_, serv_backend)
    theserver.serve_forever()    
    return 0




if (__name__ == '__main__'):
    exit(runmain())
    