# Author: Peter Jensen
#
# Convert .wav to .cas
#
# Usage: wavcas.py <input-file> <output-file>
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
  maxSampleCount = 4000  # max samples used to determine framesPerBit
  minAmplitude   = 2
  maxBitsPerByte = 13

class Params:
  inputFilename   = None
  outputFilename  = None
  verbose         = False
  silent          = False
  offsetAdjust    = False
  plot            = None
  framesPerBit    = None
  noiseWindow     = None
  dataBits        = 8
  stopBits        = 1
  bitsPerByte     = 1 + dataBits + stopBits

  @staticmethod
  def usage():
    print(
'''Converts a .wav file to a decoded binary file.  Assuming a Kansas City Standard
encoding of 18N1 (one '0' start bit, 8 data bits, and one '1' stop bit);

Invocation:
  wavcas.py [-?][-v][-s][-p n][-t n] <input file> <output file>

where:
  -?    Prints this information
  -v    Turns on verbose mode
  -s    Turns on silent mode
  -o    Use offset adjust per bit
  -n n  Noise reduction window size
  -f n  Expected frames per bit
  -t n  Number of stop bits (1 or 2). Default: 1
  -p n  Plots the input wav data for byte n. n can be specified as hex (0xnn) or decimal
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
      elif arg == '-o':
        cls.offsetAdjust = True
      elif arg == "-n":
        pi += 1
        if pi >= len(sys.argv):
          paramError('-n must be followed by a number')
        cls.noiseWindow = cls.toInt(sys.argv[pi])
        if cls.noiseWindow == None:
          cls.paramError("Illegal number syntax for -n parameter")
        if cls.noiseWindow & 1 == 0:
          cls.paramError("Odd number required for -n parameter")
      elif arg == "-f":
        pi += 1
        if pi >= len(sys.argv):
          paramError('-t must be followed by a number')
        cls.framesPerBit = cls.toInt(sys.argv[pi])
        if cls.framesPerBit == None:
          cls.paramError("Illegal number syntax for -f parameter")
      elif arg == '-p':
        pi += 1
        if pi >= len(sys.argv):
          paramError('-p must be followed by a byte number (decimal or hex)')
        cls.plot = cls.toInt(sys.argv[pi])
        if cls.plot == None:
          cls.paramError("Illegal number syntax for -p parameter")
      elif arg == '-t':
        pi += 1
        if pi >= len(sys.argv):
          paramError('-t must be followed by a number (1 or 2')
        cls.stopBits = cls.toInt(sys.argv[pi])
        if cls.stopBits == None or cls.stopBits not in [1, 2]:
          cls.paramError("Illegal value for -t parameter.  Must be 1 or 2")
        cls.bitsPerByte = 1 + cls.dataBits + cls.stopBits
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
    self.frames         = wavFile.frames

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

  def _getFramesPerBit(self, startSec = 0.0):
    if Params.framesPerBit == None:
      expectedFramesPerBit = 2*self.wavFile.frameRate/Config.baseFreq;
    else:
      expectedFramesPerBit = Params.framesPerBit
    expectedFramesPerHalfBit = expectedFramesPerBit/2
    margin = expectedFramesPerHalfBit/3
    fi = round(startSec * self.wavFile.frameRate)
    sampleCount    = 0
    sampleAcc      = 0
    while True:
      nextZero, maxSample, _ = self._getNextZeroCross(self.frames, fi)
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
    return framesPerBit, sampleCount, nextZero/self.wavFile.frameRate

  @classmethod
  def _findNextZeroBit(cls, frames, startFrame, framesPerBit):
    # find the next 3 zero crossings up->down->up

    fi = startFrame
    marginBitFrames = 0.2  * framesPerBit
    marginHalfPoint = 0.3 * framesPerBit
    while fi != None and fi < len(frames):
      crossIndex0, maxSample, crossDir = cls._getNextZeroCross(frames, fi)
      if crossDir == crossUp and maxSample > Config.minAmplitude:
        crossIndex1, _, _ = cls._getNextZeroCross(frames, crossIndex0)
        if crossIndex1 == None:
          return None
        crossIndex2, _, _ = cls._getNextZeroCross(frames, crossIndex1)
        if crossIndex2 == None:
          return None
        nFrames = crossIndex2 - crossIndex0
        if (abs(nFrames - framesPerBit) < marginBitFrames):
#            and abs((crossIndex1 - crossIndex0) - (crossIndex2 - crossIndex1)) < marginHalfPoint):
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
        return True
      framesInHalfCycle = crossIndex2 - crossIndex
      return abs(framesInHalfCycle - len(bitFrames)/2) < halfCycleMargin
    middleIndex = round(len(trimmedFrames)/2)
  #  print("middelIndex: ", middleIndex, "crossIndex: ", crossIndex, "crossDir: ", crossDir)
    middleRange = range(middleIndex-middleMargin, middleIndex+middleMargin)
    return crossIndex in middleRange

  @classmethod
  def _isZero2(cls, bitFrames):
    trimMargin   = 3
    trimmedFrames = bitFrames[trimMargin:len(bitFrames)-trimMargin]
    crossIndex, _, crossDir = cls._getNextZeroCross(trimmedFrames, 0)
    if crossDir == crossDown:
      crossIndex2, _, _ = cls._getNextZeroCross(trimmedFrames, crossIndex)
      if crossIndex2 == None:
        return True
      crossIndex3, _, _ = cls._getNextZeroCross(trimmedFrames, crossIndex2)
      return crossIndex3 == None
    else:
      return False

  @classmethod
  def _isZero3(cls, bitFrames):
    nFrames = len(bitFrames)
    margin = 0.1*nFrames
    crossIndex0, _, _ = cls._getNextZeroCross(bitFrames, 0)
    if crossIndex0 == None:
      return True
    crossIndex1, _, _ = cls._getNextZeroCross(bitFrames, crossIndex0)
    if crossIndex1 == None:
      return True
    crossIndex2, _, _ = cls._getNextZeroCross(bitFrames, crossIndex1)
    if crossIndex2 == None:
      return True
    crossIndex3, _, _ = cls._getNextZeroCross(bitFrames, crossIndex2)
    if crossIndex3 != None and crossIndex3 - crossIndex2 > margin:
      return False
    if (crossIndex1 - crossIndex0) > nFrames/2 - margin:
      return True
    if (crossIndex2 - crossIndex1) > nFrames/2 - margin:
      return True
    return False

  @staticmethod
  def _adjustOffset(bitFrames):
    mean = 0
    for bf in bitFrames:
      mean += bf
    mean = round(mean/len(bitFrames))
    newBitFrames = bytearray(len(bitFrames))
    offset = 0x80 - mean
    for bi in range(0, len(bitFrames)):
      newValue = bitFrames[bi] + offset
      if newValue < 0:
        newValue = 0
      if newValue > 0xff:
        newValue = 0xff
      newBitFrames[bi] = newValue
    return newBitFrames

  @classmethod
  def _getBits(cls, byteFrames, bitsInByte = None):
    if bitsInByte == None:
      bitsInByte = Params.bitsPerByte
    framesPerBit = len(byteFrames)/bitsInByte;
    bi = 0
    bits = ''
    bitPositions = []
    for bi in range(0, bitsInByte):
      fi = round(bi*framesPerBit)
      bitPositions.append(fi)
      if Params.offsetAdjust:
        bitFrames = cls._adjustOffset(byteFrames[fi:round(fi+framesPerBit)])
      else:
        bitFrames = byteFrames[fi:round(fi+framesPerBit)]
      if cls._isZero3(bitFrames):
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
      bitPos = cls._findNextZeroBit(allFrames, round(bitPos + 0.92*Params.bitsPerByte*framesPerBit), framesPerBit)
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

  def _getNumBitsInByte(self, frames):
    numBits = Params.bitsPerByte
    while numBits*self.framesPerBit + 0.7*self.framesPerBit < len(frames):
      numBits += 1
    return numBits
    
  def _convertToBytes(self, expectedFramesPerByte):
    byteValues = bytearray()
    for spi in range(0, len(self.startPositions)-1):
      bpStart = self.startPositions[spi]
      bpEnd   = self.startPositions[spi+1]
      byteFrames = self.frames[self.startPositions[spi]:self.startPositions[spi+1]]
      bitsInByte = self._getNumBitsInByte(byteFrames)
      if bitsInByte > Config.maxBitsPerByte:
        break
      bits, _ = self._getBits(byteFrames, bitsInByte)
      if bits[0] != '0':
        Log.error(f'Start-bit is not zero at byte: {spi}')
      if bits[9] != '1':
        Log.error(f'Stop-bit is not one at byte: {spi}')
      byteValues.append(self._toByte(bits))
    return byteValues

  @staticmethod
  def plotByteFrames(frames, bitPositions):
    fig, ax = plt.subplots(1, 1, figsize=(10,5))
    plt.grid(visible=True, which='both', axis='both')
    intFrames = [int(v)-0x80 for v in frames]
    ax.set_xticks(bitPositions)
    plt.plot(intFrames)
    plt.show()

  def plotByte(self, byteNum):
    if byteNum >= len(self.startPositions):
      Log.errorExit("Cannot plot beyond number of bytes available")
    startFrame = self.startPositions[byteNum]
    if byteNum+1 >= len(self.startPositions):
      endFrame = len(self.frames)
    else:
      endFrame = self.startPositions[byteNum+1]
    byteFrames = self.frames[startFrame:endFrame]
    bits, bitPositions = self._getBits(byteFrames, self._getNumBitsInByte(byteFrames))
    if Params.offsetAdjust:
      newByteFrames = bytearray()
      for bi in range(1, len(bitPositions)):
        newByteFrames.extend(self._adjustOffset(byteFrames[bitPositions[bi-1]:bitPositions[bi]]))
      byteFrames = newByteFrames
    byteVal = self._toByte(bits)
    secs    = self._timeStampOf(startFrame)
    Log.info(f'{byteNum:04X}: {bits} {byteVal:02X}, sampled at: {secs:.5f}s')
    if Params.verbose:
      for bi in range(1, len(bitPositions)):
        fvals = [f'{fv:02X}' for fv in byteFrames[bitPositions[bi-1]:bitPositions[bi]]]
        Log.info(f'bit: {bi-1} : {fvals}')
    self.plotByteFrames(byteFrames, bitPositions)

  def reduceNoise(self):
    nFrames = len(self.wavFile.frames)
    self.frames = bytearray(nFrames)
    value = 0
    noiseWindowHalf = Params.noiseWindow >> 1
    for fi in range(0, noiseWindowHalf):
      self.frames[fi] = self.wavFile.frames[fi]
    for ni in range(0, Params.noiseWindow):
      value += self.wavFile.frames[ni]
    for fi in range(noiseWindowHalf, nFrames - noiseWindowHalf - 1):
      self.frames[fi] = round(value/Params.noiseWindow)
      value = value + self.wavFile.frames[fi+noiseWindowHalf+1] - self.wavFile.frames[fi-noiseWindowHalf]
    for fi in range(nFrames - noiseWindowHalf - 1, nFrames):
      self.frames[fi] = self.wavFile.frames[fi]

  def process(self):
    if Params.noiseWindow != None:
      Log.progress('Reducing noise')
      self.reduceNoise()
    Log.progress('Determining frames per bit')
    framesPerBit, sampleCount, sampleTime = self._getFramesPerBit()
    self.framesPerBit = framesPerBit
    Log.info(f'Frames per bit after {sampleCount} samples: {framesPerBit:.4f}. ' +
            f'Last sample at: {sampleTime:.5f}s. ' +
            f'Real baud rate: {int(self.wavFile.frameRate/framesPerBit)}.')
    firstStartBit = self._findNextZeroBit(self.frames, 0, framesPerBit)
    Log.progress("Finding all start bits")
    startPositions = self._findStartPositions(self.frames, firstStartBit, framesPerBit)
    self.startPositions = startPositions
    lastStartBit = startPositions[-1]
    Log.info(f'Found {len(startPositions)} start bits, ' +
             f'First: {self._timeStampOf(firstStartBit):.5f}s, ' +
             f'Last: {self._timeStampOf(lastStartBit):.5f}s')
    expectedFramesPerByte = framesPerBit*Params.bitsPerByte
    Log.progress('Converting bits to bytes')
    self.allBytes = self._convertToBytes(expectedFramesPerByte)
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
