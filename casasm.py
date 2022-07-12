# Author: Peter Jensen
#
# Convert a .cas file written with NAP to a text file
#
import sys
import os
import re

class Log:
  @staticmethod
  def error(msg):
    print(f'ERROR: {msg}')

  @classmethod
  def errorExit(cls, msg):
    cls.error(msg)
    sys.exit(1)

class Params:
  inputFilename  = None
  outputFilename = None

  @staticmethod
  def paramError(msg = ''):
    if msg != '':
      Log.error(msg)
    print("Usage: " + sys.argv[0] + " <input file> [<output file>]")
    sys.exit(1)

  @classmethod
  def parse(cls):
    for p in sys.argv[1:]:
      if cls.inputFilename == None:
        cls.inputFilename = p
      elif cls.outputFilename == None:
        cls.outputFilename = p
      else:
        cls.paramError('Too many parameters')
    if cls.inputFilename == None:
      cls.paramError('Input file not specified')
    if cls.outputFilename == None:
      cls.outputFilename = os.path.splitext(os.path.basename(cls.inputFilename))[0] + '.asm'

class Lines:
  def __init__(self):
    self.lines = None

def toString(bytes):
  s = ''
  for b in bytes:
    if b >= 0x80:
      spaces = b - 0x80 + 1
      s += ' '*spaces
    else:
      s += chr(b)
  return s
  
def main():
  Params.parse()
  inputData = open(Params.inputFilename, "rb").read()
  lines = re.findall(b'\x00\x00\x00\x00\x00\x00([^\x00\xff]*)\x0d', inputData)
  for l in lines:
    print(toString(l))  

if __name__ == '__main__':
  main()
