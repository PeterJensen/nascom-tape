# Author: Peter Jensen

from collections import deque
import sys
import wave
import math

class Params:
  baseFreq  = 2400 # frequency of 1-bit
  speed     = 300  # bits per second (baud)
  stopBits  = 2
  dataBits  = 8
  leadInMin = 0.5  # minimum seconds of lead-in 1-bits
  inputFile = ''

  @classmethod
  def parseCommandLine(cls):
    cls.inputFile = sys.argv[1]

def reportError(msg):
  print(msg)
  exit(1)

def cycleCount(frames):
  count = 0
  prev  = frames[0]
  for fi in range(1, len(frames)):
    f = frames[fi]
    if prev > 0x80 and f <= 0x80:
      count += 1
    prev = f
  return count
  
def findOnes(wf, startFrame, minSec):
  wfParams = wf.getparams()
  wf.rewind()
  framesPerBit   = wfParams.framerate/Params.speed
  framesPerBitCeil = math.ceil(framesPerBit)
  cyclesPerBit = Params.baseFreq/Params.speed
  framesInLeadInMin = math.ceil(wfParams.framerate * minSec)
  print(framesInLeadInMin, cyclesPerBit)
  start = 0
  stop  = 0
  inLeadIn = False
  wf.setpos(startFrame)
  while True:
    frames = wf.readframes(framesPerBitCeil)
    if not frames:
      break
    cycles = cycleCount(frames)
    if cycles >= cyclesPerBit-1 and cycles <= cyclesPerBit+1:
      if not inLeadIn:
        inLeadIn = True
        start = wf.tell() - framesPerBitCeil
    else:
      stop = wf.tell() - framesPerBitCeil
      #print(inLeadIn, cycles, start, stop, '(', stop-start, ')')
      if inLeadIn and (stop - start) >= framesInLeadInMin:
        return start, stop
      inLeadIn = False
  return None, None

def main():
  Params.parseCommandLine()
  wf = wave.open(Params.inputFile, 'rb')
  wfParams = wf.getparams()
  print(wfParams)
  leadStart, leadStop = findOnes(wf, 0, Params.leadInMin)
  print(leadStart/wfParams.framerate, '(', leadStart, ')', leadStop/wfParams.framerate, '(', leadStop, ')')
  tailStart, tailStop = findOnes(wf, leadStop, Params.leadInMin)
  print(tailStart/wfParams.framerate, '(', tailStart, ')', tailStop/wfParams.framerate, '(', tailStop, ')')
  wf.close()

if __name__ == '__main__':
  main()