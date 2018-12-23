from pymtl import *
from bitutil import clog2


class FreeListFL( Model ):

  def __init__( self, nslots ):

    self.nbits = clog2( nslots )
    self.free_list = [ Bits( self.nbits ) for _ in range( nslots ) ]

    ncount_bits = clog2( nslots + 1 )
    self.size = Bits( ncount_bits )
    self.head = Bits( self.nbits )
    self.tail = Bits( self.nbits )

  def xtick( self ):
    if self.reset:
      for x in range( len( self.free_list ) ):
        self.free_list[ x ] = Bits( self.nbits, x )

      self.head = Bits( self.nbits, 0 )
      self.tail = Bits( self.nbits, 0 )
      self.size = Bits( self.nbits, 0 )

  def wrap_incr( self, x ):
    if x == len( self.free_list ) - 1:
      return Bits( x.nbits, 0 )
    else:
      return x + 1

  def wrap_decr( self, x ):
    if x == 0:
      return Bits( x.nbits, len( self.free_list ) - 1 )
    else:
      return x - 1

  # Returns either the tag or None if full
  def alloc( self ):
    if self.size == len( self.free_list ):
      return None
    ret = self.free_list[ self.head ]
    self.size += 1
    self.head = self.wrap_incr( self.head )
    return ret

  def free( self, tag ):
    self.free_list[ self.tail ] = Bits( self.nbits, tag )
    self.size -= 1
    self.tail = self.wrap_incr( self.tail )

  def line_trace( self ):
    return "hd:{}tl:{}:sz:{}".format( self.head, self.tail, self.size )

  def __str__( self ):
    if self.size == 0:
      return '[ ]'
    result = []
    cur = self.head
    while cur != self.wrap_decr( self.tail ):
      result += [ self.free_list[ cur ] ]
      cur = self.wrap_decr( cur )
    return str( result )