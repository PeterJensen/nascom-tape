# Author: Peter Jensen
#
# convert .nas format to .cas format
#

import sys

def error(msg):
  print("ERROR: " + msg)
  sys.exit(1)

class NasFile:
  def __init__(self, filename):
    try:
      self.lines = [l.strip() for l in open(filename, 'r').readlines()]
    except:
      error("Cannot open input file: " + nasFilename)
  def getBlock(self, offset, maxBytes):
    # 8 bytes per line
    li = offset >> 3
    numLines = maxBytes >> 3
    if li >= len(self.lines) or self.lines[li] == '.':
      return None, bytearray()
    startAddress = int(self.lines[li][0:4], 16)
    data = bytearray()
    for l in self.lines[li:li+numLines]:
      if l[0] == '.':
        break
      data.extend(bytearray.fromhex(l[5:5+8*3]))
    return startAddress, data

class Params:
  def parse(self):
    if len(sys.argv) < 3:
      print("Usage: " + sys.argv[0] + " <input .nas file> <output .cas file>")
      error("Unexpected invocation")
    self.nasFilename = sys.argv[1]
    self.casFilename = sys.argv[2]

class CasFile:
  def __init__(self, filename):
    try:
      self.file   = open(filename, "wb")
      self.blocks = []
    except:
      error("Cannot open output file: " + filename)

  class FileHeader:
    @classmethod
    def encode(cls):
      return bytes([0]*256)

  class Block:
    def __init__(self):
      self.startAddress = 0 # 2 bytes
      self.len          = 0 # 1 byte 
      self.count        = 0 # 1 byte
      self.checksum     = 0 # 1 byte
      self.data         = None

    def headerChecksum(self):
      return ((self.startAddress & 0xff) + (self.startAddress >> 8) +
              self.len + self.count) & 0xff

    def dataChecksum(self):
      checksum = 0
      for b in self.data:
        checksum += b
      return checksum & 0xff

    def encode(self):
      enc = bytearray([0, 0xff, 0xff, 0xff, 0xff]) # block start marker
      enc.extend(bytes([self.startAddress & 0xff, self.startAddress >> 8]))
      enc.append(self.len & 0xff)
      enc.append(self.count)
      enc.append(self.checksum)
      enc.extend(self.data)
      enc.append(self.dataChecksum())
      enc.extend(bytes([0]*10)) # block end marker
      return enc

  def addBlock(self, startAddress, bytes):
    block              = self.Block()
    block.startAddress = startAddress
    block.len          = len(bytes)
    block.data         = bytes
    self.blocks.append(block)

  def patchBlocks(self):
    count = len(self.blocks) - 1
    for b in self.blocks:
      b.count = count
      count -= 1
      b.checksum = b.headerChecksum()

  def write(self):
    self.patchBlocks()
    self.file.write(self.FileHeader.encode())
    for b in self.blocks:
      self.file.write(b.encode())

  def close(self):
    self.file.close()

def main():
  params = Params()
  params.parse()
  nasFile = NasFile(params.nasFilename)
  casFile = CasFile(params.casFilename)
  nasOffset = 0
  address, data = nasFile.getBlock(nasOffset, 256)
  numberOfBlocks = 0
  numberOfBytes  = 0
  startAddress   = address
  while len(data) > 0:
    casFile.addBlock(address, data)
    nasOffset += len(data)
    address, data = nasFile.getBlock(nasOffset, 256)
    numberOfBlocks += 1
    numberOfBytes  += len(data)
  casFile.write()
  casFile.close()
  print(f'Start:{startAddress:04x} Bytes:{numberOfBytes:04x}')
  
if __name__ == "__main__":
  main()
