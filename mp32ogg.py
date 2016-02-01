#!/usr/bin/python3
#

import os
import argparse
import subprocess

_debug_ = False
_decode_ = '/usr/bin/lame --decode '
_normal_ = '/usr/bin/normalize '
_encode_ = 'oggenc -q7 --output='

# Debug printer
def dprint(data = '', force = False):
	if ((_debug_ == False) and (force == False)): return
	if (data == ''):
		print('dprint() called with no data!')
		return
	print(data)

def runmain():
	global _debug_
	global _decode_
	global _normal_
	global _encode_
	parser = argparse.ArgumentParser(description = 'Python3 script to convert mp3s to oggs.')
	parser.add_argument("input_directory", help = "Input Music Folder (mp3)")
	parser.add_argument("output_directory", help = "Output Music Folder (ogg)")
	parser.add_argument("-v", "--verbose", help = "Show debug information", action = "store_true")
	args = parser.parse_args()
	_working_ = args.input_directory
	_outputs_ = args.output_directory
	if (args.verbose): _debug_ = True
	if (not os.path.exists(_outputs_)):
		dprint('Creating directory: ' + _outputs_)
		try: os.makedirs(_outputs_)
		except: raise
	for root, folders, files in os.walk(_working_):
		for folder in folders:
			newfold = os.path.join(root, folder).replace(_working_, _outputs_)
			if (not os.path.exists(newfold)):
				dprint('Creating directory: ' + newfold)
				try: os.makedirs(newfold)
				except: raise
		x = 0
		for file in files:
			fullname = os.path.join(root, file)
			if (file.lower()[-4:] == '.mp3'):
				x += 1
				song = file[:-4]
				cleaname = fullname[:-4]
				wavename = cleaname + '.wav'
				oggname = cleaname + '.ogg'
				dprint('[' + str(x) + '/' + str(len(files)) + '] - Found: ' + fullname, True)
				dprint('Decoding: ' + song)
				decode = _decode_ + '"' + fullname + '"'
				proc1 = subprocess.run(decode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)
				dprint('Normalizing: ' + song)
				normal = _normal_ + '"' + wavename + '"'
				proc2 = subprocess.run(normal, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)			
				dprint('Encoding: ' + song)
				encode = _encode_ + '"' + oggname + '" "' + wavename + '"'
				proc3 = subprocess.run(encode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)
				dprint('Cleaning up temporary wav file')
				os.remove(wavename)
				dprint('Re-locating ' + oggname + ' => ' + _outputs_)
				os.rename(oggname, oggname.replace(_working_, _outputs_))
				dprint('----------------------------------------------------------------------', True)
			else: dprint('Ignoring: ' + fullname)
	return 0

if (__name__ == '__main__'):
	exit(runmain())
