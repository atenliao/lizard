import pytest
from pymtl import *
from tests.context import lizard
from lizard.util.test_utils import run_test_vector_sim
from lizard.util.rtl.freelist import FreeList
from tests.config import test_verilog
from lizard.util.fl.freelist import FreeListFL
from lizard.model.wrapper import wrap_to_cl, wrap_to_rtl
from lizard.model.test_model import run_test_state_machine


def test_basic():
  run_test_vector_sim(
      FreeList(4, 1, 1, False, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 1, 0b0010, 0, 0),
          (0, 1, '?', '?', 1, 0),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 2, 0b0100, 0, 0),
          (1, 1, 3, 0b1000, 0, 0),
          (0, 0, '?', '?', 1, 1),
          (1, 1, 1, 0b0010, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_used_initial():
  run_test_vector_sim(
      FreeList(4, 1, 1, False, False, 2), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 2, 0b0100, 0, 0),
          (1, 1, 3, 0b1000, 0, 0),
          (0, 0, '?', '?', 1, 0),
          (1, 1, 0, 0b0001, 0, 0),
          (0, 0, '?', '?', 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_reverse_free_order():
  run_test_vector_sim(
      FreeList(2, 1, 1, False, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 1, 0b0010, 0, 0),
          (0, 0, '?', '?', 1, 1),
          (1, 1, 1, 0b0010, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_bypass():
  run_test_vector_sim(
      FreeList(2, 1, 1, True, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 1, 0b0010, 0, 0),
          (1, 1, 1, 0b0010, 1, 1),
          (1, 1, 0, 0b0001, 1, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_release():
  run_test_vector_sim(
      FreeList(4, 1, 1, False, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0] release_call release_mask'
          ),
          (1, 1, 0, 0b0001, 0, 0, 0, 0b0000),
          (1, 1, 1, 0b0010, 0, 0, 0, 0b0000),
          (1, 1, 2, 0b0100, 0, 0, 1, 0b0011),
          (1, 1, 0, 0b0001, 1, 1, 0, 0b0000),
          (1, 1, 1, 0b0010, 1, 0, 0, 0b0000),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_cl_adapter():
  run_test_vector_sim(
      wrap_to_rtl(FreeListFL(4, 1, 1, False, False)), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 1, 0b0010, 0, 0),
          (0, 1, '?', '?', 1, 0),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 2, 0b0100, 0, 0),
          (1, 1, 3, 0b1000, 0, 0),
          (0, 0, '?', '?', 1, 1),
          (1, 1, 1, 0b0010, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=False)


@pytest.mark.parametrize("model", [FreeList, FreeListFL])
def test_method(model):
  freelist = wrap_to_cl(model(4, 2, 1, True, False))
  freelist.reset()

  alloc = freelist.alloc[0]()
  assert alloc.index == 0
  assert alloc.mask == 0b0001
  freelist.cycle()

  alloc = freelist.alloc[1]()
  assert alloc.index == 1
  assert alloc.mask == 0b0010
  freelist.cycle()

  alloc1 = freelist.alloc()
  alloc2 = freelist.alloc()
  freelist.release(0b0011)
  assert alloc1.index == 2
  assert alloc2.index == 3
  assert alloc1.mask == 0b0100
  assert alloc2.mask == 0b1000
  freelist.cycle()

  freelist.free(0b0001)
  alloc = freelist.alloc()
  assert alloc.index == 0
  assert alloc.mask == 0b0001
  freelist.cycle()

  freelist.reset()
  freelist.cycle()

  alloc = freelist.alloc[0]()
  assert alloc.index == 0
  assert alloc.mask == 0b0001
  freelist.cycle()

  alloc = freelist.alloc[1]()
  assert alloc.index == 1
  assert alloc.mask == 0b0010
  freelist.cycle()


def test_state_machine():
  run_test_state_machine(FreeList, FreeListFL, (4, 2, 1, True, False))
