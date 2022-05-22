# Author: Peter Jensen
#
# Convert .wav to .cas
#
# Usage: caswav <input-file> <output-file>
#
# Wav file (unsigned 8 bit samples):
#  0: 1 cycle of 1200Hz
#  1: 2 cycles of 2400Hz
#  A byte is encoded as (18N1):
#    0:     start-bit
#    d0-d7: data bits
#    1:     stop-bit

import sys
import wave
import matplotlib.pyplot as plt

# Poor man's enum
crossUp   = 1
crossDown = 2

# Error and information output control
class Log:
  @staticmethod
  def errorExit(msg):
    print("ERROR: " + msg)
    sys.exit(1)

  @staticmethod
  def error(msg):
    print("ERROR: " + msg)

  @staticmethod
  def info(msg):
    if not Params.silent:
      print(msg)

  @staticmethod
  def progress(msg):
    if not Params.silent:
      print(msg + '...')

  @staticmethod
  def verbose(msg):
    if (Params.verbose):
      print(msg)

class Config:
  baseFreq       = 2400  # frequency of 1-bit
  bitsPerByte    = 10    # 1 start-bit, 8 data bits, 1 stop-bit
  maxSampleCount = 4000  # max samples used to determine framesPerBit

class Params:
  inputFilename  = None
  outputFilename = None
  verbose        = False
  silent         = False
  plot           = None

  @staticmethod
  def usage():
    print(
'''Converts a .wav file to a decoded binary file.  Assuming a Kansas City Standard
encoding of 18N1 (one '0' start bit, 8 data bits, and one '1' stop bit);

Invocation:
  wavcas.py [-?][-v][-s][-p n] <input file> <output file>

where:
  -?    Prints this information
  -v    Turns on verbose mode
  -s    Turns on silent mode
  -p n  Plots the input wav data for bit n. n can be specified as hex (0xnn) or decimal
''')

  @staticmethod
  def paramError(msg = ''):
    if msg != '':
      Log.error(msg)
    print("Usage: " + sys.argv[0] + " [-?][-v][-p n] <input file> <output file>")
    print("Use -? to see detailed usage information")
    sys.exit(1)

  @classmethod
  def toInt(cls, s):
    try:
      if s[0:2] == '0x':
        return int(s[2:], 16)
      else:
        return int(s)
    except:
      return None

  @classmethod
  def parse(cls):
    pi = 1
    while pi < len(sys.argv):
      arg = sys.argv[pi]
      if arg == '-?':
        cls.usage()
        sys.exit(0)
      elif arg == '-v':
        cls.verbose = True
      elif arg == '-s':
        cls.silent = True
      elif arg == '-p':
        pi += 1
        if pi >= len(sys.argv):
          paramError('-p must be followed by a byte number (decimal or hex)')
        cls.plot = cls.toInt(sys.argv[pi])
        if cls.plot == None:
          cls.paramError("Illegal number syntax for -p parameter")
      else:
        if cls.inputFilename == None:
          cls.inputFilename = arg
        elif cls.outputFilename == None:
          cls.outputFilename = arg
        else:
          cls.paramError("Only two parameters allowed")
      pi += 1
    if cls.inputFilename == None:
      cls.paramError("Input file not specified")
    if cls.outputFilename == None:
      cls.paramError("Output file not specified")

class WavFile:
  def __init__(self, filename):
    try:
      wf = wave.open(filename, 'rb')
      wfParams = wf.getparams()
      self.frames = wf.readframes(wfParams.nframes)
      self.frameRate = wfParams.framerate
      wf.close()
    except Exception as notFound:
      Log.errorExit(notFound.args[1] + ": " + filename)
    except wave.Error as waveError:
      Log.errorExit("Cannot parse input file: " + filename + " (" + waveError.args[0] + ")")

class WavData:
  def __init__(self, wavFile):
    self.wavFile = wavFile
    self.startPositions = None
    self.framesPerBit   = None

  @staticmethod
  def _getNextZeroCross(frames, startFrame):
    if startFrame == None or startFrame >= len(frames):
      return None, None, None
    fi  = startFrame
    startVal = frames[startFrame]
    maxSample = 0
    fi += 1
    while fi < len(frames):
      if frames[fi-1] > 0x80 and frames[fi] <= 0x80:
        return fi, maxSample, crossDown
      elif frames[fi-1] < 0x80 and frames[fi] >= 0x80:
        return fi, maxSample, crossUp
      sample = abs(frames[fi] - 0x80)
      if maxSample < sample:
        maxSample = sample
      fi += 1
    return None, None, None

  @classmethod
  def _getFramesPerBit(cls, wavFile, startSec = 0.0):
    expectedFramesPerBit = 2*wavFile.frameRate/Config.baseFreq;
    expectedFramesPerHalfBit = expectedFramesPerBit/2
    margin = expectedFramesPerHalfBit/3
    fi = round(startSec * wavFile.frameRate)
    sampleCount    = 0
    sampleAcc      = 0
    while True:
      nextZero, maxSample, _ = cls._getNextZeroCross(wavFile.frames, fi)
      if nextZero == None:
        break
      nFrames = nextZero - fi
      if (abs(nFrames - expectedFramesPerHalfBit) < margin and
          maxSample > 0x40):
        sampleCount += 1
        sampleAcc += nFrames
      if sampleCount >= Config.maxSampleCount:
        break
      fi = nextZero
    framesPerBit   = 2*sampleAcc/sampleCount
    return framesPerBit, sampleCount, nextZero/wavFile.frameRate

  @classmethod
  def _findNextZeroBit(cls, frames, startFrame, framesPerBit):
    # find the next 3 zero crossings up->down->up
    Found = False
    fi = startFrame
    marginBitFrames = 0.2  * framesPerBit
    marginHalfPoint = 0.25 * framesPerBit
    foundCount = 0
    while fi != None and fi < len(frames):
      crossIndex0, _, crossDir = cls._getNextZeroCross(frames, fi)
      if crossDir == crossUp:
        crossIndex1, _, _ = cls._getNextZeroCross(frames, crossIndex0)
        if crossIndex1 == None:
          return None
        crossIndex2, _, _ = cls._getNextZeroCross(frames, crossIndex1)
        if crossIndex2 == None:
          return None
        nFrames = crossIndex2 - crossIndex0
        if (abs(nFrames - framesPerBit) < marginBitFrames and
            abs((crossIndex1 - crossIndex0) - (crossIndex2 - crossIndex1)) < marginHalfPoint):
          foundCount += 1
          return crossIndex0
      fi = crossIndex0
    return None

  @classmethod
  def _isZero(cls, bitFrames):
    trimMargin   = 2
    middleMargin = 4
    halfCycleMargin = 3
    trimmedFrames = bitFrames[trimMargin:len(bitFrames)-trimMargin]
    crossIndex, _, crossDir = cls._getNextZeroCross(trimmedFrames, 0)
    if crossDir == crossUp:
      crossIndex2, _, crossDir = cls._getNextZeroCross(trimmedFrames, crossIndex)
      if crossIndex2 == None:
        return False
      framesInHalfCycle = crossIndex2 - crossIndex
      return abs(framesInHalfCycle - len(bitFrames)/2) < halfCycleMargin
    middleIndex = round(len(trimmedFrames)/2)
  #  print("middelIndex: ", middleIndex, "crossIndex: ", crossIndex, "crossDir: ", crossDir)
    middleRange = range(middleIndex-middleMargin, middleIndex+middleMargin)
    return crossIndex in middleRange

  @classmethod
  def _getBits(cls, byteFrames):
    framesPerBit = len(byteFrames)/Config.bitsPerByte;
    bi = 0
    bits = ''
    bitPositions = []
    for bi in range(0, Config.bitsPerByte):
      fi = round(bi*framesPerBit)
      bitPositions.append(fi)
      if cls._isZero(byteFrames[fi:round(fi+framesPerBit)]):
        bits += '0'
      else:
        bits += '1'
    bitPositions.append(len(byteFrames))
    return bits, bitPositions

  @classmethod
  def _findStartPositions(cls, allFrames, startFrame, framesPerBit):
    startPositions = []
    bitPos = startFrame
    while bitPos < len(allFrames):
      startPositions.append(bitPos)
      bitPos = cls._findNextZeroBit(allFrames, round(bitPos + 0.90*Config.bitsPerByte*framesPerBit), framesPerBit)
      if bitPos == None:
        break
    return startPositions

  @staticmethod
  def _toByte(bits):
    byteVal = 0
    bitVal = 1
    for b in bits[1:9]:
      if b == '1':
        byteVal += bitVal
      bitVal = bitVal << 1
    return byteVal

  def _timeStampOf(self, frameNum):
    return frameNum/self.wavFile.frameRate

  @classmethod
  def _convertToBytes(cls, allFrames, startPositions, expectedFramesPerByte):
    byteValues = bytearray()
    for spi in range(0, len(startPositions)-1):
      bpStart = startPositions[spi]
      bpEnd   = startPositions[spi+1]
      if bpEnd - bpStart > 1.5*expectedFramesPerByte:
        break
      byteFrames = allFrames[startPositions[spi]:startPositions[spi+1]]
      if len(byteFrames) > 1.1*expectedFramesPerByte:
        byteFrames = byteFrames[0:round(expectedFramesPerByte)]
      bits, _ = cls._getBits(byteFrames)
      if bits[0] != '0':
        Log.error(f'Start-bit is not zero at byte: {spi}')
      if bits[9] != '1':
        Log.error(f'Stop-bit is not one at byte: {spi}')
      byteValues.append(cls._toByte(bits))
    return byteValues

  @staticmethod
  def plotByteFrames(frames):
    fig, ax = plt.subplots(1, 1, figsize=(10,5))
    plt.grid(visible=True, which='both', axis='both')
    intFrames = [int(v)-0x80 for v in frames]
    framesPerBit = len(intFrames)/Config.bitsPerByte
    ticks = [round(framesPerBit*i) for i in range(0, Config.bitsPerByte+1)]
    ax.set_xticks(ticks)
    plt.plot(intFrames)
    plt.show()

  def plotByte(self, byteNum):
    if byteNum >= len(self.startPositions):
      Log.errorExit("Cannot plot beyond number of bytes available")
    startFrame = self.startPositions[byteNum]
    if byteNum+1 >= len(self.startPositions):
      endFrame = len(self.wavFile.frames)
    else:
      endFrame = self.startPositions[byteNum+1]
    byteFrames = self.wavFile.frames[startFrame:endFrame]
    expectedFramesPerByte = self.framesPerBit*Config.bitsPerByte
    if len(byteFrames) > 1.1*expectedFramesPerByte:
      # sometimes there are multiple stop bits for some reason
      byteFrames = byteFrames[0:round(expectedFramesPerByte)]
    bits, _ = self._getBits(byteFrames)
    byteVal = self._toByte(bits)
    secs    = self._timeStampOf(startFrame)
    Log.info(f'{byteNum:04X}: {bits} {byteVal:02X}, sampled at: {secs:.5f}s')
    self.plotByteFrames(byteFrames)

  def process(self):
    Log.progress("Determining frames per bit")
    framesPerBit, sampleCount, sampleTime = self._getFramesPerBit(self.wavFile)
    self.framesPerBit = framesPerBit
    Log.info(f'Frames per bit after {sampleCount} samples: {framesPerBit:.4f}. ' +
            f'Last sample at: {sampleTime:.5f}s. ' +
            f'Real baud rate: {int(2*self.wavFile.frameRate/framesPerBit)}.')
    firstStartBit = self._findNextZeroBit(self.wavFile.frames, 0, framesPerBit)
    Log.progress("Finding all start bits")
    startPositions = self._findStartPositions(self.wavFile.frames, firstStartBit, framesPerBit)
    self.startPositions = startPositions
    lastStartBit = startPositions[-1]
    Log.info(f'Found {len(startPositions)} start bits, ' +
             f'First: {self._timeStampOf(firstStartBit):.5f}s, ' +
             f'Last: {self._timeStampOf(lastStartBit):.5f}s')
    expectedFramesPerByte = framesPerBit*Config.bitsPerByte
    Log.progress('Converting bits to bytes')
    self.allBytes = self._convertToBytes(self.wavFile.frames, startPositions, expectedFramesPerByte)
    Log.info(f'Number of bytes: {len(self.allBytes)}')

  def writeToFile(self, filename):
    try:
      casFile = open(Params.outputFilename, "wb")
    except:
      Log.errorExit("Cannot write to output file: " + filename)
    else:
      casFile.write(self.allBytes)
      casFile.close()

def main():
  Params.parse()
  wf = WavFile(Params.inputFilename)
  wd = WavData(wf)
  wd.process()
  Log.progress("Writing to output file: " + Params.outputFilename)
  wd.writeToFile(Params.outputFilename)
  if Params.plot != None:
    wd.plotByte(Params.plot)
  return

if __name__ == '__main__':
  main()
