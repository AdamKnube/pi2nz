#!/usr/bin/env python3
#

import os
import shutil
import argparse
import threading
import subprocess
from time import sleep, gmtime, strftime

_debug_ = False
_decode_ = '/usr/bin/ffmpeg'
_normal_ = '/usr/bin/normalize --clipping '
_enc2ogg_ = '/usr/bin/oggenc -q7 --downmix --output='
_enc2mp3_ = '/usr/bin/lame -ah '


def time_stamp():
	return strftime("[%H:%M:%S] ", localtime())

def dprint(data = '', force = False):
	if ((_debug_ == False) and (force == False)): return
	if (data == ''): data = 'dprint() called with no data!'
	print(time_stamp() + data)

class convert_thread(threading.Thread):
	def __init__(self, name = '', path = '', input_dir = '', output_dir = '', temp_dir = '', encoder = ''):
		threading.Thread.__init__(self)
		self.filename = name
		self.filepath = path
		self.toplevel = input_dir
		self.move2dir = output_dir
		self.tempdir = temp_dir
		self.encoder = encoder

	def run(self):
		global _decode_
		global _normal_
		global _encode_
		songname = self.filename[:-4]
		cleaname = self.filepath[:-4]
		wavname = os.path.join(self.tempdir,  songname + '-' + str(self.ident) + '.wav')
		encname = wavname + '.enc'
		outname = cleaname.replace(self.toplevel, self.move2dir) + '.ogg'
		dprint('Decoding: ' + songname)
		decode = _decode_ + ' -i "' + self.filepath + '" -vn -acodec pcm_u8 -ar 44100 -y "' + wavname + '"'
		proc1 = subprocess.run(decode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)
		dprint('Normalizing: ' + songname)
		normal = _normal_ + '"' + wavname + '"'
		proc2 = subprocess.run(normal, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)			
		dprint('Re-Encoding: ' + songname)
		if (self.encoder.find('lame') < 0): encode = self.encoder + '"' + encname + '" "' + wavname + '"'
		else: 
			encode = self.encoder + '"' + wavname + '" "' + encname + '"'
			outname = cleaname.replace(self.toplevel, self.move2dir) + '.mp3'
		proc3 = subprocess.run(encode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)
		dprint('Cleaning up temporary wav file')
		os.remove(wavname)
		dprint('Re-locating ' + encname + ' => ' + self.move2dir)
		shutil.move(encname , outname)
		
# Main()
def runmain():
	global _debug_
	parser = argparse.ArgumentParser(description = 'Python3 script to convert mp3s to oggs.')
	parser.add_argument("input_directory", help = "Input Music Folder (mp3)")
	parser.add_argument("output_directory", help = "Output Music Folder (ogg)")
	parser.add_argument("-t", "--temp_directory", help = "Use This Temporary Directory (/tmp/mp32ogg/)")
	parser.add_argument("-v", "--verbose", help = "Show debug information", action = "store_true")
	parser.add_argument("-m", "--max_threads", help = "Maximum number of threads allowed", type = int)
	parser.add_argument("-3", "--mp3", help = "Encode to mp3 instead of ogg", action = "store_true")
	args = parser.parse_args()
	working = args.input_directory
	outputs = args.output_directory
	if (args.verbose): _debug_ = True
	max_threads = 1
	if (args.max_threads): max_threads = args.max_threads
	tempdir = '/tmp/mp32ogg'
	if (args.temp_directory): tempdir = args.temp_directory
	global _enc2ogg_
	encoder = _enc2ogg_
	if (args.mp3): 
		global _enc2mp3_
		encoder = _enc2mp3_
	if (not os.path.exists(outputs)):
		dprint('Creating directory: ' + outputs)
		try: os.makedirs(outputs)
		except: raise
	if (not os.path.exists(tempdir)):
		dprint('Creating directory: ' + tempdir)
		try: os.makedirs(tempdir)
		except: raise		
	if (working[len(working) - 1] == '/'): working = working[:-1]
	if (outputs[len(outputs) - 1] == '/'): outputs = outputs[:-1]
	if (tempdir[len(tempdir) - 1] == '/'): tempdir = tempdir[:-1]
	for root, folders, files in os.walk(working):
		for folder in folders:
			newfold = os.path.join(root, folder).replace(working, outputs)
			if (not os.path.exists(newfold)):
				dprint('Creating directory: ' + newfold)
				try: os.makedirs(newfold)
				except: raise
		x = 0
		thread_pool = []
		for file in files:
			x += 1
			fullname = os.path.join(root, file)
			if (file.lower()[-4:] == '.mp3'):
				dprint('[' + str(x) + '/' + str(len(files)) + '] - Found: ' + fullname, True)
				is_running = False
				while (not is_running):
					if (threading.active_count() < (max_threads + 1)):
						thread_pool.append(convert_thread(file, fullname, working, outputs, tempdir, encoder))
						thread_pool[len(thread_pool) - 1].start()
						is_running = True
					else: sleep(0.1)
			else: dprint('[' + str(x) + '/' + str(len(files)) + '] - Ignored: ' + fullname)
	return 0

if (__name__ == '__main__'):
	exit(runmain())
