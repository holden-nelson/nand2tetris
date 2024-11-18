import sys
import os

class HackSymbols:
  ARegister = 'A'
  DRegister = 'D'
  SelectedRamRegister = 'M'
  StackPointer = 'SP'
  LocalPointer = 'LCL'
  ArgPointer = 'ARG'
  ThisPointer = 'THIS'
  ThatPointer = 'THAT'
  R13Register = 'R13'
  R14Register = 'R14'
  R15Register = 'R15'

class VmSegments:
  Argument = 'argument'
  Local = 'local'
  Static = 'static'
  Constant = 'constant'
  This = 'this'
  That = 'that'
  Pointer = 'pointer'
  Temp = 'temp'

  @classmethod
  def matchSegment(cls, cmd):
    for attr_name, attr_value in vars(cls).items():
      if attr_value == cmd:
        return getattr(cls, attr_name)
    return None

  @classmethod
  def getHackSymbol(cls, segment):
      segment_to_symbol = {
          cls.Argument: HackSymbols.ArgPointer,
          cls.Local: HackSymbols.LocalPointer,
          cls.Static: '16', 
          cls.Constant: None, 
          cls.This: HackSymbols.ThisPointer,
          cls.That: HackSymbols.ThatPointer,
          cls.Pointer: 3,
          cls.Temp: '5'
      }
      return segment_to_symbol.get(segment, None)

class VmCommands:
  # push / pop
  Push = 'push'
  Pop = 'pop'
  PushPopCommands = (Push, Pop)

  # arithmetic
  Add = 'add'
  Subtract = 'sub'
  Negate = 'neg'
  ArithmeticCommands = (Add, Subtract, Negate)

  # comparison
  Equals = 'eq'
  GreaterThan = 'gt'
  LessThan = 'lt'
  ComparisonCommands = (Equals, GreaterThan, LessThan)

  # logical
  And = 'and'
  Or = 'or'
  Not = 'not'
  LogicalCommands = (And, Or, Not)

  @classmethod
  def matchCommand(cls, cmd):
    for attr_name, attr_value in vars(cls).items():
      if attr_value == cmd:
        return getattr(cls, attr_name)
    return None


class VirtualMachine:

  def __init__(self, filename):
    self.inFilename = filename
    self.inFile = None
    self.comparisonCounter = 0

    name, _ = os.path.splitext(filename)
    self.outFilename = name + '.asm'

  def __enter__(self):
    self.inFile = open(self.inFilename, 'r')
    self.outFile = open(self.outFilename, 'w')
    return self

  def __exit__(self, exc_type, exc_Val, exc_tb):
    if self.inFile:
      self.inFile.close()

    if self.outFile:
      self.outFile.close()

  def translate(self):
    for line in self.inFile:
      instruction = line.strip()
      if not instruction: continue
      if instruction[:2] == '//': continue
      self.parseCommand(instruction)

      print(f'found instruction: {instruction}')

  def parseCommand(self, command):
    operation, *operands = command.split()

    match operation:
      case _ if operation in VmCommands.PushPopCommands:
        segment = VmSegments.matchSegment(operands[0])
        value = operands[1]

        if operation == VmCommands.Push: 
          self.handlePush(value, segment)

        if operation == VmCommands.Pop:
          self.handlePop(value, segment)

      case _ if operation in VmCommands.ArithmeticCommands:
        if operation == VmCommands.Add:
          self.handleAdd()

        if operation == VmCommands.Subtract:
          self.handleSubtract()

        if operation == VmCommands.Negate:
          self.handleNegate()

      case _ if operation in VmCommands.ComparisonCommands:
        if operation == VmCommands.Equals:
          self.handleEquals()
        if operation == VmCommands.GreaterThan:
          self.handleGreaterThan()
        if operation == VmCommands.LessThan:
          self.handleLessThan()

      case _ if operation in VmCommands.LogicalCommands:
        if operation == VmCommands.And:
          self.handleAnd()
        if operation == VmCommands.Or:
          self.handleOr()
        if operation == VmCommands.Not:
          self.handleNot()

  def handlePush(self, value, segment):
    if segment == VmSegments.Constant:
      self.pushConstant(value)
    if segment in [ VmSegments.Local, VmSegments.Argument, VmSegments.This, VmSegments.That ]:
      self.pushLocalArgThisThat(segment, value)
    if segment == VmSegments.Static:
      self.pushStatic(value)
    if segment == VmSegments.Temp:
      self.pushTemp(value)
    if segment == VmSegments.Pointer:
      self.pushPointer(value)

  def handlePop(self, value, segment):
    if segment in [ VmSegments.Local, VmSegments.Argument, VmSegments.This, VmSegments.That ]:
      self.popLocalArgThisThat(segment, value)
    if segment == VmSegments.Static:
      self.popStatic(value)
    if segment == VmSegments.Temp:
      self.popTemp(value)
    if segment == VmSegments.Pointer:
      self.popPointer(value)

  def push(self, comp):
    self.writeAInstruction(HackSymbols.StackPointer)
    self.writeCInstruction(dest=HackSymbols.ARegister, comp=HackSymbols.SelectedRamRegister)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=comp)
    self.incrementStackPointer()

  def pop(self, dest):
    self.decrementStackPointer()
    self.writeCInstruction(dest=dest, comp=HackSymbols.SelectedRamRegister)

  def pushConstant(self, value):
    self.writeAInstruction(value)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.ARegister)

    self.push(comp=HackSymbols.DRegister)

  def pushLocalArgThisThat(self, segment, value):
    self.writeComment(f'pushing the value in {segment} {value} onto stack')
    self.loadSegmentOffsetAddress(segment, value)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.SelectedRamRegister)
    self.push(HackSymbols.DRegister)

  def pushStatic(self, value):
    self.writeComment(f'pushing static {value} onto stack')
    self.loadStaticOffset(value)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.SelectedRamRegister)
    self.push(HackSymbols.DRegister)

  def pushTemp(self, value):
    self.writeComment(f'pushing temp {value} onto stack')
    self.loadTempOffset(value)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.SelectedRamRegister)
    self.push(HackSymbols.DRegister)

  def pushPointer(self, value):
    pointer = 'THIS' if value == '0' else 'THAT'
    self.writeComment(f'pushing pointer {value} ({pointer}) onto stack')
    self.writeAInstruction(pointer)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.SelectedRamRegister)
    self.push(HackSymbols.DRegister)

  def popLocalArgThisThat(self, segment, value):
    self.writeComment(f'popping the top of stack into {segment} {value}')
    self.loadSegmentOffsetAddress(segment, value, dest=HackSymbols.DRegister)
    self.writeAInstruction(HackSymbols.R13Register)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=HackSymbols.DRegister)

    self.pop(HackSymbols.DRegister)
    self.writeAInstruction(HackSymbols.R13Register)
    self.writeCInstruction(dest=HackSymbols.ARegister, comp=HackSymbols.SelectedRamRegister)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=HackSymbols.DRegister)

  def popStatic(self, value):
    self.writeComment(f'popping the top of stack into static {value}')
    self.loadStaticOffset(value, dest=HackSymbols.DRegister)
    self.writeAInstruction(HackSymbols.R13Register)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=HackSymbols.DRegister)

    self.pop(HackSymbols.DRegister)
    self.writeAInstruction(HackSymbols.R13Register)
    self.writeCInstruction(dest=HackSymbols.ARegister, comp=HackSymbols.SelectedRamRegister)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=HackSymbols.DRegister)

  def popTemp(self, value):
    self.writeComment(f'popping the top of stack into temp {value}')
    self.loadTempOffset(value, dest=HackSymbols.DRegister)
    self.writeAInstruction(HackSymbols.R13Register)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=HackSymbols.DRegister)

    self.pop(HackSymbols.DRegister)
    self.writeAInstruction(HackSymbols.R13Register)
    self.writeCInstruction(dest=HackSymbols.ARegister, comp=HackSymbols.SelectedRamRegister)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=HackSymbols.DRegister)

  def popPointer(self, value):
    pointer = 'THIS' if value == '0' else 'THAT'
    self.writeComment(f'popping stack into pointer {value} ({pointer})')
    self.pop(HackSymbols.DRegister)
    self.writeAInstruction(pointer)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=HackSymbols.DRegister)

  def handleAdd(self):
    self.writeComment(f'Adding top two stack values')
    self.pop(dest=HackSymbols.DRegister)

    self.decrementStackPointer()
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'{HackSymbols.DRegister}+{HackSymbols.SelectedRamRegister}')
    self.incrementStackPointer()

  def handleSubtract(self):
    self.writeComment(f'Subtracting top two stack values')
    self.pop(dest=HackSymbols.DRegister)

    self.decrementStackPointer()
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'{HackSymbols.SelectedRamRegister}-{HackSymbols.DRegister}')
    self.incrementStackPointer()

  def handleNegate(self):
    self.writeComment('Negating top of stack')
    self.decrementStackPointer()
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'-{HackSymbols.SelectedRamRegister}')
    self.incrementStackPointer()

  def handleEquals(self):
    self.writeComment('Comparing top two stack values: equals')
    self.pop(dest=HackSymbols.DRegister)

    self.decrementStackPointer()
    self.writeCInstruction(
      dest=HackSymbols.DRegister, 
      comp=f'{HackSymbols.SelectedRamRegister}-{HackSymbols.DRegister}')

    self.writeAInstruction(f'TRUE_{self.comparisonCounter}')
    self.writeCInstruction(comp=HackSymbols.DRegister, jump='JEQ')

    self.pushFalseResult(f'RETURN_EQ_{self.comparisonCounter}')
    self.pushTrueResult(f'RETURN_EQ_{self.comparisonCounter}')
    self.writeLabel(f'RETURN_EQ_{self.comparisonCounter}')
    self.comparisonCounter += 1

  def handleGreaterThan(self):
    self.writeComment('Comparing top two stack values: greaterThan')
    self.pop(dest=HackSymbols.DRegister)

    self.decrementStackPointer()
    self.writeCInstruction(
      dest=HackSymbols.DRegister, 
      comp=f'{HackSymbols.SelectedRamRegister}-{HackSymbols.DRegister}')

    self.writeAInstruction(f'TRUE_{self.comparisonCounter}')
    self.writeCInstruction(comp=HackSymbols.DRegister, jump='JGT')

    self.pushFalseResult(f'RETURN_EQ_{self.comparisonCounter}')
    self.pushTrueResult(f'RETURN_EQ_{self.comparisonCounter}')
    self.writeLabel(f'RETURN_EQ_{self.comparisonCounter}')
    self.comparisonCounter += 1

  def handleLessThan(self):
    self.writeComment('Comparing top two stack values: lessThan')
    self.pop(dest=HackSymbols.DRegister)

    self.decrementStackPointer()
    self.writeCInstruction(
      dest=HackSymbols.DRegister, 
      comp=f'{HackSymbols.SelectedRamRegister}-{HackSymbols.DRegister}')

    self.writeAInstruction(f'TRUE_{self.comparisonCounter}')
    self.writeCInstruction(comp=HackSymbols.DRegister, jump='JLT')

    self.pushFalseResult(f'RETURN_EQ_{self.comparisonCounter}')
    self.pushTrueResult(f'RETURN_EQ_{self.comparisonCounter}')
    self.writeLabel(f'RETURN_EQ_{self.comparisonCounter}')
    self.comparisonCounter += 1

  def handleAnd(self):
    self.writeComment('ANDing top two stack values')
    self.pop(dest=HackSymbols.DRegister)

    self.decrementStackPointer()
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'{HackSymbols.DRegister}&{HackSymbols.SelectedRamRegister}')
    self.incrementStackPointer()

  def handleOr(self):
    self.writeComment('ORing top two stack values')
    self.pop(dest=HackSymbols.DRegister)

    self.decrementStackPointer()
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'{HackSymbols.DRegister}|{HackSymbols.SelectedRamRegister}')
    self.incrementStackPointer()

  def handleNot(self):
    self.writeComment('NOTting top of stack')
    self.decrementStackPointer()
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'!{HackSymbols.SelectedRamRegister}')
    self.incrementStackPointer()

  def incrementStackPointer(self):
    self.writeAInstruction(HackSymbols.StackPointer)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'{HackSymbols.SelectedRamRegister}+1')
    self.writeCInstruction(dest=HackSymbols.ARegister, comp=HackSymbols.SelectedRamRegister)

  def decrementStackPointer(self):
    self.writeAInstruction(HackSymbols.StackPointer)
    self.writeCInstruction(dest=HackSymbols.SelectedRamRegister, comp=f'{HackSymbols.SelectedRamRegister}-1')
    self.writeCInstruction(dest=HackSymbols.ARegister, comp=HackSymbols.SelectedRamRegister)

  def pushTrueResult(self, returnLabel):
    self.writeLabel(f'TRUE_{self.comparisonCounter}')
    self.writeAInstruction('1')
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=f'-{HackSymbols.ARegister}')
    self.push(comp=HackSymbols.DRegister)

    self.writeAInstruction(returnLabel)
    self.writeCInstruction(comp='0', jump='JMP')

  def pushFalseResult(self, returnLabel):
    self.writeLabel(f'FALSE_{self.comparisonCounter}')
    self.pushConstant('0')
    self.writeAInstruction(returnLabel)
    self.writeCInstruction(comp='0', jump='JMP')

  def pushInfiniteLoop(self):
    self.writeLabel('LOOP')
    self.writeAInstruction('LOOP')
    self.writeCInstruction(comp='0', jump='JMP')

  def loadSegmentOffsetAddress(self, segment, offset, dest=HackSymbols.ARegister):
    self.writeAInstruction(offset)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.ARegister)

    segmentPointer = VmSegments.getHackSymbol(segment)
    self.writeAInstruction(segmentPointer)
    self.writeCInstruction(dest=dest, comp=f'{HackSymbols.DRegister}+{HackSymbols.SelectedRamRegister}')

  def loadStaticOffset(self, offset, dest=HackSymbols.ARegister):
    self.writeAInstruction(offset)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.ARegister)

    staticBase = VmSegments.getHackSymbol('static')
    self.writeAInstruction(staticBase)
    self.writeCInstruction(dest=dest, comp=f'{HackSymbols.DRegister}+{HackSymbols.ARegister}')

  def loadTempOffset(self, offset, dest=HackSymbols.ARegister):
    self.writeAInstruction(offset)
    self.writeCInstruction(dest=HackSymbols.DRegister, comp=HackSymbols.ARegister)

    staticBase = VmSegments.getHackSymbol('temp')
    self.writeAInstruction(staticBase)
    self.writeCInstruction(dest=dest, comp=f'{HackSymbols.DRegister}+{HackSymbols.ARegister}')

  def writeLabel(self, label):
    self.outFile.write(f'({label})\n')

  def writeComment(self, comment):
    self.outFile.write(f'// {comment}\n')

  def writeAInstruction(self, source):
    self.outFile.write(f'@{source}\n')

  def writeCInstruction(self, comp, dest='', jump=''):
    if dest != '': dest = f'{dest}='
    if jump != '': jump= f';{jump}'

    self.outFile.write(f'{dest}{comp}{jump}\n')

  def writeEmptyLine(self):
    self.outFile.write('\n')


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print("Usage: translate.py <filename>")
    sys.exit(1)

  filename = sys.argv[1]

  with VirtualMachine(filename) as vm:
    vm.translate();
