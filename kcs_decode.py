#!/usr/bin/env python3
# kcs_decode.py
#
# Author : David Beazley (http://www.dabeaz.com)
# Copyright (C) 2010
#
# Requires Python 3.1.2 or newer

"""
Converts a WAV file containing Kansas City Standard data and
extracts text data from it. See:

http://en.wikipedia.org/wiki/Kansas_City_standard
"""

from collections import deque
from itertools import islice

# Base frequency (representing a 1)
BASE_FREQ = 2400
NOISE_MARGIN = 4
NOISE_MARGIN_UPPER = 0x80 + NOISE_MARGIN
NOISE_MARGIN_LOWER = 0x80 - NOISE_MARGIN
SKIP_LEAD_SECS = 0.5

def trim_frames(wf):
    samplewidth = wf.getsampwidth()
    nchannels = wf.getnchannels()
    framerate = wf.getframerate()
    use_data = False
    frames_to_skip = int(framerate*SKIP_LEAD_SECS)
    skipped_frames = 0
    frame_num = 0

    while True:
        frames = wf.readframes(8192)
        if not frames:
            break
        data_bytes = bytes(frames[samplewidth-1::samplewidth*nchannels])
        for b in data_bytes:
            if use_data:
                if skipped_frames > frames_to_skip:
                    yield frame_num, b
                else:
                    skipped_frames = skipped_frames + 1
            elif b >= NOISE_MARGIN_UPPER or b <= NOISE_MARGIN_LOWER:
                use_data = True
            frame_num = frame_num + 1

def dump_frames(wavefile):
    samplewidth = wavefile.getsampwidth()
    nchannels = wavefile.getnchannels()
    previous = 0
    while True:
        frames = wavefile.readframes(100)
        if not frames:
            break
        print('Frames: ', frames[samplewidth-1::samplewidth*nchannels].hex())
        break

def dump_bytes(wf):
    framerate = wf.getframerate()
    trimmed_frames = islice(trim_frames(wf), 0, 100);
    start_frame, val = next(trimmed_frames)
    print('Start Frame: ', start_frame, ' (', start_frame/framerate, ')')
    print('Bytes:  ', bytes([val] + [b for fn, b in trimmed_frames]).hex());

# Generate a sequence representing sign bits
def generate_wav_sign_change_bits(wavefile):
    samplewidth = wavefile.getsampwidth()
    nchannels = wavefile.getnchannels()
    previous = 0
    while True:
        frames = wavefile.readframes(8192)
        if not frames:
            break

        # Extract most significant bytes from left-most audio channel
        msbytes = bytearray(frames[samplewidth-1::samplewidth*nchannels])

        # Emit a stream of sign-change bits
        for byte in msbytes:
            signbit = byte & 0x80
            yield 1 if (signbit ^ previous) else 0
            previous = signbit

def generate_wav_sign_change_bits_stream(stream):
    previous = 0
    for (fn, b) in stream:
        signbit = b & 0x80
        if signbit != previous:
            yield (fn, 1)
        else:
            yield (fn, 0)
        previous = signbit

def sign_sum(l):
    sum = 0;
    for fn, s in l:
       sum += s
    return sum

# Generate a sequence of data bytes by sampling the stream of sign change bits
def generate_bytes(bitstream,framerate):
    bitmasks = [0x1,0x2,0x4,0x8,0x10,0x20,0x40,0x80]

    # Compute the number of audio frames used to encode a single data bit
    frames_per_bit = float(framerate)*8/BASE_FREQ
    print("frames_per_bit: ", frames_per_bit)
    frames_per_bit = int(round(frames_per_bit))

    # Queue of sampled sign bits
    sample = deque(maxlen=frames_per_bit)     

    # Fill the sample buffer with an initial set of data
    sample.extend(islice(bitstream,frames_per_bit-1))
    #print(sample)
    sign_changes = sign_sum(sample)
    #print("sign_changes:", sign_changes)

    # Look for the start bit
    for (fn, val) in bitstream:
        if val:
            sign_changes += 1
        if sample.popleft()[1]:
            sign_changes -= 1
        sample.append((fn,val))
    
        # If a start bit is detected, sample the next 8 data bits
        if sign_changes <= 9:
            #print("start bit found: ", sample[0])
            byteval = 0
            for mask in bitmasks:
                slice = [elem for elem in islice(bitstream,frames_per_bit)]
                print("slice:", slice)
                #print("sign_sum(slice):", sign_sum(slice))
                if sign_sum(slice) >= 12:
                    byteval |= mask
            yield byteval
            # Skip the final two stop bits and refill the sample buffer 
            sample.extend(islice(bitstream,2*frames_per_bit,3*frames_per_bit-1))
            sign_changes = sign_sum(sample)
            #print("sign_changes:", sign_changes)

if __name__ == '__main__':
    import wave
    import sys
    import optparse

    p = optparse.OptionParser()
    p.add_option("-b",action="store_true",dest="binary")
    p.add_option("--binary",action="store_true",dest="binary")
    p.set_defaults(binary=False)

    opts, args = p.parse_args()
    if len(args) != 1:
        print("Usage: %s [-b] infile" % sys.argv[0],file=sys.stderr)
        raise SystemExit(1)

    wf = wave.open(args[0])
    print('framerate: ', wf.getframerate())
    print('samplewidth: ', wf.getsampwidth())
    print('nchannels: ', wf.getnchannels())
    #dump_frames(wf)
    #dump_bytes(wf)
    #exit()

    trimmed_frames = trim_frames(wf)
    sign_changes = generate_wav_sign_change_bits_stream(trimmed_frames)
    byte_stream  = generate_bytes(sign_changes, wf.getframerate())

    if opts.binary:
        # Output the byte stream in 80-byte chunks with NULL stripping
        outf = sys.stdout.buffer.raw
        while True:
            buffer = bytes(islice(byte_stream,80))
            if not buffer:
                break
            print(buffer.hex())
            #outf.write(buffer)
    else:
        buffer = bytearray()
        while True:
            linebreak = buffer.find(b'\n')
            if linebreak >= 0:
                line = buffer[:linebreak+1].replace(b'\r\n',b'\n')
                sys.stdout.write(line.decode('latin-1'))
                del buffer[:linebreak+1]
            else:
                fragment = bytes(byte for byte in islice(byte_stream,80) if byte)
                if not fragment:
                    sys.stdout.write(buffer.decode('latin-1'))
                    break
                buffer.extend(fragment)
