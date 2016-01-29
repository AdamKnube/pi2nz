#!/usr/bin/env python3
#

import os
import pygame
import random
import argparse
import threading
import http.server
import urllib.parse
from time import sleep

_debug_ = False                                     # debug mode
_bind_port_ = 80                                    # bind port
_bind_address_ = ''                                 # bind address
_music_folder_ = '/'                                # music folder
_killer_ = None                                     # shutdown thread
_the_list_ = None                                   # the playlist
_the_tunez_ = None                                  # music thread
_the_server_ = None                                 # webserver thread

# Debug printer
def dprint(data = '', force = False):
    if ((_debug_ == False) and (force == False)): return
    if (data == ''): 
        print('dprint() called with no data!')
        return
    print(data)
           
# Make an array of mp3 files    
def getMusic(where = ''):
    templist = []
    dprint('Searching: ' + _music_folder_)
    for root, folders, files in os.walk(where):
        for thisfile in files:
            absolute = os.path.join(root, thisfile)    
            if ( thisfile[-4:].lower() == '.ogg'):
                templist.append(absolute)
                dprint('Added: ' + thisfile)
            else: dprint('Ignored: ' + thisfile + ' (' + thisfile[-4:].lower() + ')')
    return templist

# Music player
class tunez_machine(threading.Thread):   
    def __init__(self, music_list):
        dprint('Music thread initializing...')
        threading.Thread.__init__(self)
        self.current = -1
        self.active = True
        self.playing = False        
        self.shuffle = False     
        self.wasstopped = False
        if (self.shuffle): self.thelist = shuffle(music_list)
        else: self.thelist = sorted(music_list)
        pygame.mixer.init()                
    
    def run(self):
        dprint("Music thread running.")
        while (self.active):
            if ((self.playing == True) and (pygame.mixer.music.get_busy() == 0)):
                if ((self.current < 0) or (self.current >= len(self.thelist))):
                    dprint('Starting for the first time or looping around the list.')
                    self.current = 0
                elif(self.wasstopped):
                    self.wasstopped = False
                else:
                    dprint('The song, "' + self.thelist[self.current] + '" has ended.')                
                    pygame.mixer.music.stop()
                    self.current += 1
                dprint('Loading "' + self.thelist[self.current] + '".')
                pygame.mixer.music.load(self.thelist[self.current])
                dprint('Starting playback.')
                pygame.mixer.music.play()
            elif (self.playing == False) and (pygame.mixer.music.get_busy() > 0):
                pygame.mixer.music.stop()
            sleep(0.5)            
        dprint('Music thread dies.')
                
    def search(self, search = ''):
        dprint('Searching for: ' + search)
        found = []
        findstr = '<br><font size=+2><u>Search Results:</u></font><br>'
        isfound = False
        for index in range(0, len(self.thelist)):
            if (self.thelist[index].lower().find(search.lower()) > -1): 
                dprint('Found (' + search + ') in "' + self.thelist[index] + '".')
                found.append(index)
                isfound = True
        if (isfound):
            for find in found: 
                findstr = findstr + '<a href="/?force=' + str(find) + '">'
                findstr = findstr + self.thelist[find][(len(_music_folder_)+1):] + '</a><br>'
            return findstr
        else: return '"' + search + '" not found in list.'
    
    def force(self, index):
        if ((index > -1) and (index < len(self.thelist))):
            if (self.playing): self.play()
            self.current = index
            self.play()
            return index
    
    def play(self):
        dprint('Toggling PLAY mode:')
        if (self.playing == True): 
            dprint('Stop.')
            self.playing = False
            self.wasstopped = True
            while (pygame.mixer.music.get_busy() > 0): sleep(0.5)
            return 'Stopped'
        else: 
            dprint('Play.')
            self.playing = True
            while (pygame.mixer.music.get_busy() == 0): sleep(0.5)
            return 'Playing'
        
    def find(self, what=''):
        for x in range(0, len(self.thelist)-1):
            if (self.thelist[x] == what): return x
        return 0
    
    def random(self):
        dprint('Toggling SHUFFLE mode:')
        tmp = ''
        retstr = ''
        newlist = sorted(self.thelist)
        if (self.current > -1): tmp = self.thelist[self.current]
        if (self.shuffle):
            self.shuffle = False
            dprint('Shuffle is off.')
            retstr = 'Shuffle Off'
        else:
            random.shuffle(newlist)
            self.shuffle = True
            dprint('Shuffle is on.')
            retstr = 'Shuffle On' 
        self.thelist = newlist
        if (self.current > -1): self.current = self.find(tmp)
        return retstr 
    
    def status(self):
        thestr = 'Playing: ' + str(self.playing) + ', Shuffle: ' + str(self.shuffle) + '\n'
        if (self.current > -1): thestr = thestr + '<br>[' + str(self.current+1) + '/' + str(len(self.thelist)) + '] ' + self.thelist[self.current] + '\n'
        return thestr
    
    def die(self):
        if (self.playing): self.play()
        self.active = False
   
# Webserver backend
class serv_backend(http.server.BaseHTTPRequestHandler):
    global _the_tunez_   
    def do_HEAD(self):
        dprint(self.requestline)
        
    def do_GET(self):
        dprint(self.requestline)
        isquery = self.path.find('?')
        if (isquery > -1):
            dprint('Found GET query.')
            query = urllib.parse.parse_qs(self.path[isquery+1:])
            if (len(query)):
                for key in query:
                    dprint('Found key: ' + key)
                    if (key == 'force'):
                        force1 = query[key][0]
                        forced = int(force1)
                        thetune = _the_tunez_.thelist[_the_tunez_.force(forced)]
                        self.showpage('Forcing ' + str(forced) + ': ' + thetune[len(_music_folder_)+1:])
                        return
                    elif (key == 'halt'):
                        self.showpage('Shutting Down')
                        _killer_.start()
                        return
            else: 
                dprint('Rejecting blank or malformed query')
        self.showpage()
                 
    def do_POST(self):
        dprint(self.requestline)
        setq = ''
        sets = False
        length = int(self.headers['Content-Length'])
        post_data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
        for item in post_data:
            if (item == 'play'):
                _the_tunez_.play()
                self.showpage()
                return
            elif (item == 'search'):
                sets = True
            elif(item == 'query'):
                setq = str(post_data['query'])
            elif (item == 'shuffle'):
                _the_tunez_.random()
                self.showpage()
                return 
            elif (item == 'next'):
                test = _the_tunez_.current + 1
                if (test >= len(_the_tunez_.thelist)): test = 0
                _the_tunez_.current = test
                if (_the_tunez_.playing):     
                    _the_tunez_.play()
                    _the_tunez_.play()
                self.showpage()
                return
            elif (item == 'back'):
                test = _the_tunez_.current - 1
                if (test < 0): test = len(_the_tunez_.thelist) - 1
                _the_tunez_.current = test
                if (_the_tunez_.playing):     
                    _the_tunez_.play()
                    _the_tunez_.play()
                self.showpage()
                return
            elif (item == 'halt'):
                _killer_.start()
                return
        if ((sets == True) and (setq != '')): 
            self.showpage(_the_tunez_.search(setq[2:-2]))
            return
        dprint('POST request had no usable variables.')
        self.showpage()

    def showpage(self, info = ''):
        global _bind_port_
        global _bind_address_
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b'<html><head><title>pi2nz</title></head><body bgcolor="#000000" text="#FFFFFF">\n')
        self.wfile.write(b'<center><h1><font color="#00FF00">pi2nz web interface</font></h1></center>')
        if (info == ''): self.wfile.write(b'<center>' + _the_tunez_.status().encode('utf-8') + b'</center><br>')
        else: self.wfile.write(b'<center>' + info.encode('utf-8') + b'</center><br>')
        wtf = self.requestline.split('/')
        self.wfile.write(b'<form action="http://' + wtf[2].encode('utf-8') + b':' + str(_bind_port_).encode('utf-8') + b'/" method="POST">\n')
        self.wfile.write(b'<center><table width=100%>')
        self.wfile.write(b'<tr>')
        self.wfile.write(b'<td align=center><input type="text" name="query" value="" /></td>\n')
        self.wfile.write(b'<td align=center><input type="submit" name="search" value="Search" /></td>\n')
        self.wfile.write(b'</tr><tr>')
        self.wfile.write(b'<td align=center><input type="submit" name="play" value="Play/Stop" /></td>\n')
        self.wfile.write(b'<td align=center><input type="submit" name="shuffle" value="Shuffle" /></td>\n')
        self.wfile.write(b'</tr><tr>')
        self.wfile.write(b'<td align=center><input type="submit" name="back" value="<= Back" /></td>\n')
        self.wfile.write(b'<td align=center><input type="submit" name="next" value="Next =>" /></td>\n')        
        self.wfile.write(b'</tr></table><br>')
        self.wfile.write(b'<input type="submit" name="halt" value="Halt" />')
        self.wfile.write(b'</center></form></body></html>\n\n')

class kthread(threading.Thread):
    global _the_tunez_
    global _the_server_
    def run(self):
        _the_tunez_.die()
        _the_server_.shutdown()

def runmain():
    global _debug_
    global _the_list_
    global _bind_port_
    global _bind_address_
    global _music_folder_    
    global _the_tunez_
    global _the_server_
    global _killer_
    parser = argparse.ArgumentParser(description = 'Python3 music player with http remote control.')
    parser.add_argument("root", help = "Music Folder")
    parser.add_argument("-a", "--address", help = "Bind Address")
    parser.add_argument("-p", "--port", help = "Bind Port", type = int)
    parser.add_argument("-d", "--debug", help = "Debug Output", action = "store_true")
    args = parser.parse_args()
    if (args.debug): _debug_ = True
    if (args.address): _bind_address_ = args.address
    if (args.port): _bind_port_ = args.port
    if (args.root): _music_folder_ = args.root
    _killer_ = kthread()
    dprint('Searching for OGG files in ' + _music_folder_ + '.', True)
    _the_list_ = getMusic(_music_folder_)
    dprint('Starting music player with ' + str(len(_the_list_)) + ' songs.', True)    
    _the_tunez_ = tunez_machine(_the_list_)
    _the_tunez_.start()
    dprint('Starting webserver at http://' + _bind_address_ + ':' + str(_bind_port_) + '/.', True)
    _the_server_ = http.server.HTTPServer((_bind_address_, _bind_port_), serv_backend)
    _the_server_.serve_forever()
    _the_tunez_.join()
    dprint('Goodbye.', True)
    return 0

if (__name__ == '__main__'):
    exit(runmain())
    