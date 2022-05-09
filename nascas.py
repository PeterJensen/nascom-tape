# Author: Peter Jensen
#
# Convert between .nas and .cas formats
#
# Usage: nascas <input-file> <output-file>
#
# Input file type is automatically detected.  If input file type is .nas,
# output file type will be .cas and vice versa
#
import sys
import re

def error(msg):
  print("ERROR: " + msg)
  sys.exit(1)

class Params:
  def parse(self):
    if len(sys.argv) < 3:
      print("Usage: " + sys.argv[0] + " <input file> <output file>")
      error("Unexpected invocation")
    self.inputFilename = sys.argv[1]
    self.outputFilename = sys.argv[2]

class InputData:
  def __init__(self):
    self.startAddress = None
    self.data = bytearray()
  def initWithNas(self, filename):
    try:
      lines = [l.strip() for l in open(filename, 'r').readlines()]
    except:
      error("Cannot open input file: " + filename)
    else:
      # 8 bytes per line
      for line in lines:
        if line[0] == '.':
          break
        if self.startAddress == None:
          self.startAddress = int(line[0:4], 16)
        self.data.extend(bytes.fromhex(line[5:5+8*3]))
  def initWithCas(self, filename):
    try:
      file = open(filename, 'rb')
    except:
      error("Cannot open input file: " + filename)
    else:
      content = file.read()
      i = 256 # skip over the first 256 zeros
      while i < len(content):
        i += 5 # skip over block start marker
        if self.startAddress == None:
          self.startAddress = content[i] + 256*content[i+1]
        blockLength = content[i+2]
        blockCount  = content[i+3]
        if blockLength == 0:
          blockLength = 256
        i += 5 # skip over block header
        checksum = self.computeChecksum(content[i:i+blockLength])
        self.data.extend(content[i:i+blockLength])
        i += blockLength
        if checksum != content[i]:
          print(f'Unexpected checksum in block: {blockCount}. {checksum:02X} != {content[i]:02X}')
        i += 1 # skip over data checksum
        i += 10 # skip over block end marker
        if blockCount == 0:
          break

class CasFile:
  class FileHeader:
    @staticmethod
    def encode():
      return bytes([0]*256)

  class Block:
    def __init__(self, startAddress, length, count, data):
      self.startAddress = startAddress # 2 bytes
      self.length       = length       # 1 byte 
      self.count        = count        # 1 byte
      self.checksum     = 0            # 1 byte
      self.data         = data

    def headerChecksum(self):
      return ((self.startAddress & 0xff) + (self.startAddress >> 8) +
              self.length + self.count) & 0xff

    def dataChecksum(self):
      checksum = 0
      for b in self.data:
        checksum += b
      return checksum & 0xff

    def encode(self):
      enc = bytearray([0, 0xff, 0xff, 0xff, 0xff]) # block start marker
      enc.extend(bytes([self.startAddress & 0xff, self.startAddress >> 8]))
      enc.append(self.length & 0xff)
      enc.append(self.count)
      enc.append(self.headerChecksum())
      enc.extend(self.data)
      enc.append(self.dataChecksum())
      enc.extend(bytes([0]*10)) # block end marker
      return enc

  @staticmethod
  def isValid(filename):
    try:
      file = open(filename, "rb")
    except:
      return False
    else:
      headerBytes = file.read(256)
      file.close()
      return headerBytes == bytes([0]*256)

  def __init__(self, inputData, filename):
    self.inputData = inputData
    try:
      self.file   = open(filename, "wb")
    except:
      error("Cannot open output file: " + filename)

  def write(self):
    self.file.write(self.FileHeader.encode())
    blockSize = 256
    di = 0
    addr = self.inputData.startAddress
    count = (len(self.inputData.data) + blockSize - 1) // blockSize - 1
    while di < len(self.inputData.data):
      data = self.inputData.data[di:di+blockSize]
      block = self.Block(addr, len(data), count, data)
      self.file.write(block.encode())
      count -= 1
      addr += blockSize
      di += blockSize
    self.file.close()

class NasFile:
  class Line:
    def __init__(self, startAddress, data):
      self.startAddress = startAddress
      self.data = data
    
    def computeChecksum(self):
      checksum = (self.startAddress & 0xff) + (self.startAddress >> 8)
      for b in self.data:
        checksum += b
      return checksum & 0xff

    def encode(self):
      startString = '{0:02X}{1:02X}'.format(self.startAddress >> 8, self.startAddress & 0xff)
      enc = bytearray(startString, 'utf-8')
      enc.append(ord(' '))
      dataStr = ' '.join([f'{b:02X}' for b in self.data])
      enc.extend(bytes(dataStr, 'utf-8'))
      enc.append(ord(' '))
      checksum = self.computeChecksum()
      enc.extend(bytes(f'{checksum:02X}', 'utf-8'))
#      enc.extend(b'\x08\x08\x0a')
      enc.extend(b'\x08\x08\x0d\x0a')
      return enc

  def isValid(filename):
    try:
      file = open(filename, "rb")
    except:
      return False
    else:
      firstLine = file.read(5 + 9*3 + 3)
      syntaxRe = b'[0-9A-F]{4}( [0-9A-F][0-9A-F]){9}\x08\x08\x0a'
      result = re.search(syntaxRe, firstLine)
      file.close()
      return result != None

  def __init__(self, inputData, filename):
    self.inputData = inputData
    try:
      self.file   = open(filename, "wb")
    except:
      error("Cannot open output file: " + filename)

  def write(self):
    di = 0
    lineDataSize = 8
    addr = self.inputData.startAddress
    while di < len(self.inputData.data):
      lineData = self.inputData.data[di:di+lineDataSize]
      while len(lineData) < lineDataSize:
        lineData.append(0x00)
      line = self.Line(addr, lineData)
      self.file.write(line.encode())
      di += lineDataSize
      addr += lineDataSize
    self.file.write(bytes([ord('.'), 0xa]))
    self.file.close()

def main():
  params = Params()
  params.parse()
  inputData = InputData()
  if CasFile.isValid(params.inputFilename):
    print("Converting CAS to NAS")
    inputData.initWithCas(params.inputFilename)
    nasFile = NasFile(inputData, params.outputFilename)
    nasFile.write()
  elif NasFile.isValid(params.inputFilename):
    print("Converting NAS to CAS")
    inputData.initWithNas(params.inputFilename)
    casFile = CasFile(inputData, params.outputFilename)
    casFile.write()
  else:
    error("Input file is not a valid NAS or CAS file")

if __name__ == "__main__":
  main()
