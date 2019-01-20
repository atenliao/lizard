from pymtl import *
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz


class BugInterface:

  def __init__( s):
    s.Out = Bits( 2 )

    s.port= MethodSpec({
        'select': Bits(1),
    }, {
        'out': s.Out,
    }, False, False )


class Bug( Model ):

  def __init__( s ):
    s.interface = BugInterface()
    s.port = s.interface.port.in_port()

    s.outs = [Wire(2) for _ in range(2)]
    
    @s.combinational
    def compute_1():
      s.outs[0].v = 1

    @s.combinational
    def compute_2():
      if s.port.select:
        s.outs[1].v = 3
      else:
        s.outs[1].v = s.outs[0].v

    @s.combinational
    def compute_3():
      s.port.out.v = s.outs[1]

  def line_trace( s ):
    return "{}".format(s.port.out)

class BugMagic( Model ):

  def __init__( s ):
    s.interface = BugInterface()
    s.port = s.interface.port.in_port()

    s.outs = [Wire(2) for _ in range(2)]
    s.magiczero = Wire(2)
    s.connect(s.magiczero, 0)
    
    @s.combinational
    def compute_1():
      s.outs[s.magiczero].v = 1

    @s.combinational
    def compute_2():
      if s.port.select:
        s.outs[1].v = 3
      else:
        s.outs[1].v = s.outs[s.magiczero].v

    @s.combinational
    def compute_3():
      s.port.out.v = s.outs[1]

  def line_trace( s ):
    return "{}".format(s.port.out)
  

