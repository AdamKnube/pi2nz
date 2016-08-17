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

_version_ = 1.4                                     # version
_debug_ = False                                     # debug mode
_upload_ = False                                    # allow uploads
_killer_ = None                                     # shutdown thread
_the_tunez_ = None                                  # music thread
_the_server_ = None                                 # webserver thread

# Debug printer
def dprint(data = '', force = False):
    if ((_debug_ == False) and (force == False)): return
    if (data == ''): 
        print('dprint() called with no data!')
        return
    print(data)
           
# Music player
class tunez_machine(threading.Thread):   
    def __init__(self, music_folder, lag_timer):
        dprint('Music thread initializing...')
        threading.Thread.__init__(self)
        self.current = -1
        self.active = True
        self.playing = False        
        self.shuffle = False     
        self.lag = lag_timer
        self.was_stopped = False
        if (music_folder[len(music_folder) - 1] == '/'): music_folder = music_folder[:-1]
        self.root_folder = music_folder
        self.thelist = sorted(self.get_music(music_folder))
        pygame.mixer.init()                
    
    def is_ready(self):
        if ((self.active) and (len(self.thelist) > 0)): return True 
        return False
        
    def run(self):
        if (len(self.thelist) == 0):
            dprint('Error: No OGG files were found in: ' + self.root_folder, True)
            self.active = False
        dprint('Music thread starting with ' + str(len(self.thelist)) + ' songs.', True) 
        while (self.active):
            if ((self.playing == True) and (pygame.mixer.music.get_busy() == 0)):
                if ((self.current < 0) or (self.current >= len(self.thelist))):
                    dprint('Starting for the first time or looping around the list.')
                    self.current = 0
                elif(self.was_stopped):
                    self.was_stopped = False
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
            sleep(self.lag)            
        dprint('Music thread dies.')
        return 0

    def get_music(self, where = ''):
        templist = []
        dprint('Searching: ' + where)
        for root, folders, files in os.walk(where):
            for thisfile in files:
                absolute = os.path.join(root, thisfile)    
                if ((thisfile[-4:].lower() == '.mp3') or (thisfile[-4:].lower() == '.ogg')):
                    templist.append(absolute)
                    dprint('Added: ' + thisfile)
                else: dprint('Ignored: ' + thisfile + ' (' + thisfile[-4:].lower() + ')')
        return templist
                
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
                findstr += '<a href="/?force=' + str(find) + '">'
                findstr += self.thelist[find][(len(self.root_folder)+1):-4] + '</a><br>'
            return findstr
        else: return '"' + search + '" not found in list.'
    
    def force(self, index = 0):
        i = 0
        try: 
            i = int(index) 
            if ((i > -1) and (i < len(self.thelist))):
                if (self.playing): self.play()
                self.current = i
                self.play()
        except: pass
        finally: return i
    
    def play(self):
        dprint('Toggling PLAY mode:')
        if (self.playing == True): 
            self.playing = False
            self.was_stopped = True
            while (pygame.mixer.music.get_busy() > 0): sleep(self.lag)
        else: 
            self.playing = True
            while (pygame.mixer.music.get_busy() == 0): sleep(self.lag)
        return self.playing
    
    def find(self, what=''):
        for x in range(0, len(self.thelist)-1):
            if (self.thelist[x] == what): return x
        return 0
    
    def random(self):
        dprint('Toggling SHUFFLE mode:')
        tmp = ''
        newlist = sorted(self.thelist)
        if (self.current > -1): tmp = self.thelist[self.current]
        if (self.shuffle): self.shuffle = False
        else: 
            random.shuffle(newlist)
            self.shuffle = True
        self.thelist = newlist
        if (self.current > -1): self.current = self.find(tmp)
        return self.shuffle 
    
    def volume(self, newvol = -1):        
        if ((newvol >= 0) and (newvol <= 100)):
            dprint('Setting volumne to: ' + str(newvol))
            pygame.mixer.music.set_volume(newvol / 100)
        return pygame.mixer.music.get_volume() 
       
    def status(self):
        thestr = 'Playing: ' + str(self.playing) + ', Shuffle: ' + str(self.shuffle) + ', Volume: ' + str(int(self.volume() * 100))
        if (self.current > -1): thestr = thestr + '<br>[' + str(self.current+1) + '/' + str(len(self.thelist)) + '] ' + self.thelist[self.current][len(self.root_folder)+1:-4] + '\n'
        return thestr
    
    def die(self):
        if (self.playing): self.play()
        self.active = False
   
# Webserver backend
class serv_backend(http.server.BaseHTTPRequestHandler):
    global _debug_
    global _upload_
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
                        try: 
                            forced = int(force1)
                            if ((forced >= 0) and (forced < len(_the_tunez_.thelist))):
                                _the_tunez_.force(forced)
                                self.showpage()
                            else: int('dumbass')
                        except: self.showpage('Invalid force index: ' + force1)
                        finally: return
                    elif (key == 'halt'):
                        self.showpage('Goodbye')
                        _killer_.start()
                        return
            else: 
                dprint('Rejecting blank or malformed query')
        self.showpage()
                 
    def do_POST(self):
        dprint(self.requestline)
        length = int(self.headers['Content-Length'])
        try:
            post_data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
        except UnicodeDecodeError:
            dprint('Found undecodable binary input trying upload routines')
            self.showpage()
            return
        for item in post_data:
            if (_debug_):
                dprint('Found POST variable: ' + item.strip() + ' = ' + str(post_data[item]).strip())
            if (item == 'play'):   
                _the_tunez_.play()             
                self.showpage()
                return
            elif ((item == 'upload') and (str(post_data['ufile']) != '')):
                dprint('upload')
                self.showpage('Uploading not yet implemented.')
                return
            elif (item == 'search'):
                try:
                    query = str(post_data['query'])[2:-2]
                    self.showpage(_the_tunez_.search(query))
                except: self.showpage('Invalid search string')
                finally: return
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
                else : _the_tunez_.was_stopped = True
                self.showpage()
                return
            elif (item == 'back'):
                test = _the_tunez_.current - 1
                if (test < 0): test = len(_the_tunez_.thelist) - 1
                _the_tunez_.current = test
                if (_the_tunez_.playing):     
                    _the_tunez_.play()
                    _the_tunez_.play()
                else : _the_tunez_.was_stopped = True
                self.showpage()
                return
            elif (item == 'halt'):
                self.showpage('Goodbye')
                _killer_.start()
                return
            elif (item == 'v25'):
                _the_tunez_.volume(25)
                self.showpage()
                return
            elif (item == 'v50'):
                _the_tunez_.volume(50)
                self.showpage()
                return
            elif (item == 'v75'):
                _the_tunez_.volume(75)
                self.showpage()
                return
            elif (item == 'v100'):
                _the_tunez_.volume(100)
                self.showpage()
                return                                                                
        dprint('POST request had no usable variables.')
        self.showpage()

    def showpage(self, info = ''):
        global _version_
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b'<html><head><title>pi2nz</title></head><body bgcolor="#000000" text="#FFFFFF">\n')
        self.wfile.write(b'<center><h1><font color="#00FF00">pi2nz v' + str(_version_).encode('utf-8') + b'</font></h1></center>\n')
        self.wfile.write(b'<center><font size=+1>' + _the_tunez_.status().encode('utf-8') + b'</font></center><br>\n')
        if (info != ''): self.wfile.write(b'<center><font size=+1>' + info.encode('utf-8') + b'</font></center><br>\n')
        (who, where) = self.request.getsockname()
        self.wfile.write(b'<form action="http://' + who.encode('utf-8') + b':' + str(where).encode('utf-8') + b'/" method="POST">\n')
        self.wfile.write(b'<center><table><tr>')
        self.wfile.write(b'<td align=center colspan=2><input type="text" name="query" value="" style="width: 400px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'<td align=center colspan=2><input type="submit" name="search" value="Search" style="width: 400px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'</tr><tr>')
        self.wfile.write(b'<td align=center colspan=2><input type="submit" name="play" value="Play/Stop" style="width: 400px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'<td align=center colspan=2><input type="submit" name="shuffle" value="Shuffle" style="width: 400px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'</tr><tr>')
        self.wfile.write(b'<td align=center colspan=2><input type="submit" name="back" value="<= Back" style="width: 400px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'<td align=center colspan=2><input type="submit" name="next" value="Next =>" style="width: 400px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'</tr><tr>')
        self.wfile.write(b'<td align=center><input type="submit" name="v25" value="25%" style="width: 200px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'<td align=center><input type="submit" name="v50" value="50%" style="width: 200px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'<td align=center><input type="submit" name="v75" value="75%" style="width: 200px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'<td align=center><input type="submit" name="v100" value="100%" style="width: 200px; font-size: 50px; height: 120px"/></td>\n')
        self.wfile.write(b'</tr><tr>')
        self.wfile.write(b'<td align=center colspan=4><input type="submit" name="halt" value="Shutdown" style="width: 800px; font-size: 50px; height: 120px"/></td>\n')	
        self.wfile.write(b'</tr></table><br></center></form>\n')
        if (_upload_):
            self.wfile.write(b'<form action="http://' + who.encode('utf-8') + b':' + str(where).encode('utf-8') + b'/" method="POST" enctype="multipart/form-data">\n')
            self.wfile.write(b'<center><input type="file" name="ufile" size="40" style="width: 800px; font-size: 50px; height: 120px" /></center>\n')
            self.wfile.write(b'<center><input type="submit" name="upload" value="Upload..." style="width: 800px; font-size: 50px; height: 120px"/></center>\n')
            self.wfile.write(b'</form>\n')
        self.wfile.write(b'</body></html>\n\n')

# Exit thread
class kthread(threading.Thread):
    global _the_tunez_
    global _the_server_
    def run(self):
        _the_tunez_.die()
        _the_server_.shutdown()

# Main()
def runmain():
    global _debug_
    global _upload_
    global _killer_
    global _the_tunez_
    global _the_server_
    parser = argparse.ArgumentParser(description = 'Python3 music player with http remote control.')
    parser.add_argument("root", help = "Root music folder")
    parser.add_argument("-a", "--address", help = "Bind address")
    parser.add_argument("-p", "--port", help = "Bind port", type = int)
    parser.add_argument("-d", "--debug", help = "Debug output", action = "store_true")
    parser.add_argument("-s", "--start", help = "Start playback", action = "store_true")
    parser.add_argument("-r", "--random", help = "Start randomized", action = "store_true")
    parser.add_argument("-v", "--volume", help = "Initial volume", type = int)
    parser.add_argument("-i", "--idle", help = "Idle time for sleep timers", type = float)
    parser.add_argument("-u", "--upload", help = "Allow uploads", action = "store_true")
    args = parser.parse_args()
    if (args.debug): _debug_ = True    
    if (args.upload): _upload_ = True
    bind_port = 8080
    if (args.port): bind_port = args.port
    bind_address = ''
    if (args.address): bind_address = args.address
    lagwagon = 0.5    
    if (args.idle): lagwagon = args.idle
    _killer_ = kthread()
    dprint('Starting music player in: ' + args.root, True)    
    _the_tunez_ = tunez_machine(args.root, lagwagon)
    _the_tunez_.start()
    x = 0
    while ((not _the_tunez_.is_ready()) and (x <= (5 / lagwagon))): 
        sleep(lagwagon)
        x += 1
    if (x > (5 / lagwagon)): 
        dprint('Failed to initialize music player, aborting!', True)
        return 1
    if (args.volume): _the_tunez_.volume(args.volume)
    if (args.random): _the_tunez_.random()
    if (args.start): _the_tunez_.play()
    showaddy = bind_address
    if (showaddy == ''): showaddy = '0.0.0.0'
    dprint('Starting webserver at: http://' + showaddy + ':' + str(bind_port) + '/.', True)
    _the_server_ = http.server.HTTPServer((bind_address, bind_port), serv_backend)
    _the_server_.serve_forever()
    _the_tunez_.join()
    _killer_.join()
    dprint('Goodbye.', True)
    return 0

if (__name__ == '__main__'):
    exit(runmain())
    
