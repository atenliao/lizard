from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl.comparator import Comparator, ComparatorInterface, CMPFunc
from util.rtl.register import Register, RegisterInterface
from util.rtl.lookup_table import LookupTable, LookupTableInterface
from bitutil import clog2, clog2nz
from core.rtl.messages import DispatchMsg, ExecuteMsg, BranchType
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface
from core.rtl.kill_unit import PipelineKillDropController
from core.rtl.controlflow import KillType
from config.general import *


def BranchInterface():
  return StageInterface(DispatchMsg(), ExecuteMsg())


class BranchStage(Model):

  def __init__(s, branch_interface):
    UseInterface(s, branch_interface)
    imm_len = DispatchMsg().imm.nbits
    data_len = XLEN
    spec_idx_len = DispatchMsg().hdr_spec.nbits

    s.require(
        MethodSpec(
            'cflow_redirect',
            args={
                'spec_idx': Bits(spec_idx_len),
                'target': Bits(data_len),
                'force': Bits(1),
            },
            rets={},
            call=True,
            rdy=False,
        ),)

    s.connect(s.process_accepted, 1)

    s.cmp_ = Comparator(ComparatorInterface(data_len))
    s.msg_ = Wire(DispatchMsg())
    s.msg_imm_ = Wire(imm_len)
    s.imm_ = Wire(data_len)

    s.take_branch_ = Wire(1)
    s.branch_target_ = Wire(data_len)

    OP_LUT_MAP = {
      BranchType.BRANCH_TYPE_EQ : CMPFunc.CMP_EQ,
      BranchType.BRANCH_TYPE_NE : CMPFunc.CMP_NE,
      BranchType.BRANCH_TYPE_LT : CMPFunc.CMP_LT,
      BranchType.BRANCH_TYPE_GE : CMPFunc.CMP_GE,
    }
    s.op_lut_ = LookupTable(
        LookupTableInterface(DispatchMsg().branch_msg_type_.nbits,
                             CMPFunc.bits), OP_LUT_MAP)

    # Connect to disptach get method
    s.connect(s.msg_, s.process_in_)

    # Connect lookup opmap
    s.connect(s.op_lut_.lookup_in_, s.msg_.branch_msg_type_)
    s.connect(s.cmp_.exec_func, s.op_lut_.lookup_out)
    # Connect up cmp call
    s.connect(s.cmp_.exec_src0, s.msg_.rs1)
    s.connect(s.cmp_.exec_src1, s.msg_.rs2)
    s.connect(s.cmp_.exec_unsigned, s.msg_.branch_msg_unsigned)
    s.connect(s.cmp_.exec_call, s.process_call)

    # Connect up to controlflow redirect method
    s.connect(s.cflow_redirect_spec_idx, s.msg_.hdr_spec)
    s.connect(s.cflow_redirect_target, s.branch_target_)
    s.connect(s.cflow_redirect_force, 0)
    s.connect(s.cflow_redirect_call, s.process_call)

    @s.combinational
    def set_take_branch():
      s.take_branch_.v = 0
      # TODO handle branches that are not conditional
      s.take_branch_.v = s.cmp_.exec_res

    @s.combinational
    def set_inputs():
      # TODO set the proper compare function
      s.cmp_.exec_func.v = 0

    @s.combinational
    def compute_target():
      s.msg_imm_.v = s.msg_.imm
      # PYMTL_BROKEN: sext(s.msg_.imm) does not create valid verilog
      # Vivado errors: "range is not allowed in prefix"
      s.imm_.v = sext(s.msg_imm_, data_len)
      if s.take_branch_:
        s.branch_target_.v = s.msg_.hdr_pc + s.imm_
      else:
        s.branch_target_.v = s.msg_.hdr_pc + 4

    @s.combinational
    def set_value_reg_input():
      s.process_out.v = 0
      s.process_out.hdr.v = s.msg_.hdr


def BranchDropController():
  return PipelineKillDropController(
      DropControllerInterface(ExecuteMsg(), ExecuteMsg(),
                              KillType(MAX_SPEC_DEPTH)))


Branch = gen_stage(BranchStage, BranchDropController)