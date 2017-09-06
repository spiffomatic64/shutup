# Modified from https://stackoverflow.com/questions/4160175/detect-tap-with-pyaudio-from-live-mic

#!/usr/bin/python

# open a microphone in pyAudio and listen for taps

import pyaudio
import struct
import math
import pygame,sys
from pygame.locals import *
from datetime import datetime
from ctypes import windll, Structure, c_long, byref #windows only

screen_width = 1280
screen_height = 720

INITIAL_TAP_THRESHOLD = 0.10
FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 2
RATE = 44100  
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
# if we get this many noisy blocks in a row, increase the threshold
OVERSENSITIVE = 15.0/INPUT_BLOCK_TIME                    
# if we get this many quiet blocks in a row, decrease the threshold
UNDERSENSITIVE = 120.0/INPUT_BLOCK_TIME 
# if the noise was longer than this many blocks, it's not a 'tap'
MAX_TAP_BLOCKS = 0.15/INPUT_BLOCK_TIME

class RECT(Structure):
    _fields_ = [
    ('left',    c_long),
    ('top',     c_long),
    ('right',   c_long),
    ('bottom',  c_long),
    ]
    def width(self):  return self.right  - self.left
    def height(self): return self.bottom - self.top


def onTop(window):
    SetWindowPos = windll.user32.SetWindowPos
    GetWindowRect = windll.user32.GetWindowRect
    rc = RECT()
    GetWindowRect(window, byref(rc))
    SetWindowPos(window, -1, rc.left, rc.top, 0, 0, 0x0001)

def get_rms( block ):
    # RMS amplitude is defined as the square root of the 
    # mean over time of the square of the amplitude.
    # so we need to convert this string of bytes into 
    # a string of 16-bit samples...

    # we will get one short out for each 
    # two chars in the string.
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    # iterate over the block.
    sum_squares = 0.0
    for sample in shorts:
        # sample is a signed short in +/- 32768. 
        # normalize it to 1.0
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n

    return math.sqrt( sum_squares / count )

class TapTester(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.tap_threshold = INITIAL_TAP_THRESHOLD
        self.noisycount = MAX_TAP_BLOCKS+1 
        self.quietcount = 0 
        self.errorcount = 0

    def stop(self):
        self.stream.close()

    def find_input_device(self):
        device_index = None       

        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) ) 
                    for dev in devinfo:
                        print dev
            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                    if "C920" in devinfo["name"]:
                        device_index = i
                        return device_index

        if device_index == None:
            print( "No preferred input found; using default input device." )

        return device_index

    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(   format = FORMAT,
                                 channels = CHANNELS,
                                 rate = RATE,
                                 input = True,
                                 input_device_index = device_index,
                                 frames_per_buffer = INPUT_FRAMES_PER_BLOCK)

        return stream

    def tapDetected(self):
        print "Tap!"

    def listen(self):
        try:
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        except IOError, e:
            # dammit. 
            self.errorcount += 1
            print( "(%d) Error recording: %s"%(self.errorcount,e) )
            self.noisycount = 1
            return

        amplitude = get_rms( block )
        
        if amplitude > self.tap_threshold:
            print datetime.now().strftime('%Y/%m/%d %I:%M:%S %p'),amplitude
        return amplitude
            # noisy block
        

def main():
    pygame.init()

    DISPLAY=pygame.display.set_mode((screen_width,screen_height),0,32)

    pygame.draw.rect(DISPLAY,(0,0,255),(0,0,screen_width,screen_height))
    onTop(pygame.display.get_wm_info()['window']) 

    tt = TapTester()

    while True:
        for event in pygame.event.get():
            if event.type==QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()
        vol = tt.listen() * (255/INITIAL_TAP_THRESHOLD)
        if vol>255:
            vol=255
        if vol<0:
            vol=0
        pygame.draw.rect(DISPLAY,(vol,255-vol,0),(0,0,screen_width,screen_height))
        
main()
