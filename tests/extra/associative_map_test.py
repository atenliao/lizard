import pytest
from pymtl import *
from tests.context import lizard
from lizard.util.rtl.associative_map import BasicAssociativeMap
from lizard.model.wrapper import wrap_to_cl
from lizard.model.translate import translate

def conditional_translate(model, spec):
  if spec == 'verilate':
    model = translate(model)
  return model

@pytest.mark.parametrize('trans', ['verilate', 'sim'])
def test_full_associative(trans):
  model = conditional_translate(BasicAssociativeMap(Bits(4), Bits(8), 8, 8), trans)
  model.vcd_file = 'bob.vcd'
  df = wrap_to_cl(model)
  df.reset()

  df.read_next(0)
  df.cycle()

  assert df.read().found == 0
  df.write(key=9, remove=0, data=162)
  df.cycle()
  
  df.read_next(9)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data == 162
  df.cycle()

  df.write(key=9, remove=1, data=133)
  df.cycle()
  
  df.read_next(9)
  df.cycle()
  
  result = df.read()
  assert result.found == 0
  df.cycle()
