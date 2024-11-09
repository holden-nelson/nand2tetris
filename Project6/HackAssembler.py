import sys
import os

class Assembler:

  def __init__(self, filename):
    self.inFilename = filename
    self.inFile = None
    self.symbolTable = None

    name, _ = os.path.splitext(filename)
    self.outFilename = name + '.hack'

  def __enter__(self):
    self.inFile = open(self.inFilename, 'r')
    self.outFile = open(self.outFilename, 'w')
    return self

  def __exit__(self, exc_type, exc_Val, exc_tb):
    if self.inFile:
      self.inFile.close()

    if self.outFile:
      self.outFile.close()

  def assemble(self):
    self.symbolTable = self.SymbolTable(self.inFile)

    self.inFile.seek(0)

    for line in self.inFile:
      instruction = line.strip()
      if not instruction: continue
      assembled = self.parseInstruction(instruction)
      if assembled: self.outFile.write(assembled + '\n')


    self.symbolTable.printSymbolTable()
    
  def parseInstruction(self, instruction):

    match instruction[0]:
      case '@':
        assembled = self.handleAInstruction(instruction)
        return assembled;

      case '/':
        pass

      case '(':
        pass

      case _:
        assembled = self.handleCInstruction(instruction)
        return assembled;

  def handleCInstruction(self, instruction):
    dest, comp, jump = None, None, None

    if '=' in instruction:
      dest, instruction = instruction.split('=')

    if ';' in instruction:
      comp, jump = instruction.split(';')
    else:
      comp = instruction

    destTranslation = self.translateDest(dest) if dest else'000'
    compTranslation = self.translateComp(comp)
    jumpTranslation = self.translateJump(jump) if jump else '000'

    return f"111{compTranslation}{destTranslation}{jumpTranslation}"

  def translateDest(self, dest):
    destMapping = {
      "M":    "001",
      "D":    "010",
      "MD":   "011",
      "A":    "100",
      "AM":   "101",
      "AD":   "110",
      "ADM":  "111"
    }

    return destMapping[dest]


  def translateComp(self, comp):
    compMapping = {
      "0":   "0101010",
      "1":   "0111111",
      "-1":  "0111010",
      "D":   "0001100",
      "A":   "0110000",
      "M":   "1110000",
      "!D":  "0001101",
      "!A":  "0110001",
      "!M":  "1110001",
      "-D":  "0001111",
      "-A":  "0110011",
      "-M":  "1110011",
      "D+1": "0011111",
      "A+1": "0110111",
      "M+1": "1110111",
      "D-1": "0001110",
      "A-1": "0110010",
      "M-1": "1110010",
      "D+A": "0000010",
      "D+M": "1000010",
      "D-A": "0010011",
      "D-M": "1010011",
      "A-D": "0000111",
      "M-D": "1000111",
      "D&A": "0000000",
      "D&M": "1000000",
      "D|A": "0010101",
      "D|M": "1010101"
    }

    return compMapping[comp]
  
  def translateJump(self, jump):
    jumpMapping = {
      "JGT":  "001",
      "JEQ":  "010",
      "JGE":  "011",
      "JLT":  "100",
      "JNE":  "101",
      "JLE":  "110",
      "JMP":  "111"
    }

    return jumpMapping[jump]

  def handleAInstruction(self, instruction):
    symbol = instruction[1:]
    address = self.symbolTable.getSymbol(symbol)

    if address != None: 
      return self.translateAInstruction(address)
    else: 
      try:
        address = int(symbol)
        return self.translateAInstruction(address)
      except ValueError:
        self.symbolTable.addVariable(symbol)
        newVariableAddress = self.symbolTable.getSymbol(symbol)
        return self.translateAInstruction(newVariableAddress)

  def translateAInstruction(self, instruction):
    return f"0{bin(instruction)[2:].zfill(15)}"

  class SymbolTable:
    def __init__(self, file):
      self.customSymbolAddress = 16
      self.table = {
        "R0": 0,
        "R1": 1,
        "R2": 2,
        "R3": 3,
        "R4": 4,
        "R5": 5,
        "R6": 6,
        "R7": 7,
        "R8": 8,
        "R9": 9,
        "R10": 10,
        "R11": 11,
        "R12": 12,
        "R13": 13,
        "R14": 14,
        "R15": 15,
        "SP": 0,
        "LCL": 1,
        "ARG": 2,
        "THIS": 3,
        "THAT": 4,
        "SCREEN": 16384,
        "KBD": 24576
      }
      self.buildTableFromFile(file);

    def buildTableFromFile(self, file):
      currentMemoryAddress = 0
      
      for line in file:
        instruction = line.strip()

        if not instruction: continue

        # determine instruction type
        match instruction[0]:
          case '(': # label type
            label = instruction[1:-1]
            self.table[label] = currentMemoryAddress
            continue

          case '/':
            continue

          case _:
            pass
        
        currentMemoryAddress += 1

    def getSymbol(self, symbol):
      return self.table.get(symbol)

    def addLabel(self, symbol, address):
      self.table[symbol] = address

    def addVariable(self, variable):
      self.table[variable] = self.customSymbolAddress
      self.customSymbolAddress += 1

    def printSymbolTable(self):
      print(f"Symbol table: {self.table}")


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Usage: HackAssembly.py <filename>")
    sys.exit(1)

  filename = sys.argv[1]

  with Assembler(filename) as assembler:
    assembler.assemble();
