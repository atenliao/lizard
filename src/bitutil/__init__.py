from pymtl import *


def clog2(x):
  # Could be implemented with int(math.ceil(math.log(x, 2))),
  # but might cause strange floating point issues
  i = 0
  v = 1
  while x > v:
    v *= 2
    i += 1
  return i


def clog2nz(x):
  result = clog2(x)
  if result == 0:
    return 1
  else:
    return result


def copy_bits(bits):
  return Bits(bits.nbits, int(bits))


def sane_lookup(d):

  @staticmethod
  def f(k):
    if isinstance(k, Bits):
      k = int(k)
    return d[k]

  return f


def bit_enum(name, bits=None, *names, **pairs):
  assert not (names and pairs)
  if pairs:
    assert bits
  else:
    min_bits = clog2(len(names))
    bits = bits or clog2(len(names))
    assert bits >= min_bits

  data = {}
  short = {}
  for i, spec in enumerate(names):
    if isinstance(spec, tuple):
      key, s_key = spec
    else:
      key, s_key = spec, spec
    data[key] = Bits(bits, i)
    short[i] = s_key
  for key, value in pairs.iteritems():
    data[key] = Bits(bits, value)
    short[int(value)] = key

  names_dict = dict((int(value), key) for key, value in data.iteritems())
  data['name'] = sane_lookup(names_dict)
  data['short'] = sane_lookup(short)
  data['bits'] = bits
  result = type(name, (), data)

  @staticmethod
  def lookup(k):
    if hasattr(result, k):
      return getattr(result, k)
    else:
      return None

  @staticmethod
  def contains(k):
    return int(k) in names_dict

  result.lookup = lookup
  result.contains = contains

  return result


def bslice(high, low=None):
  """
  Represents: the bits range [high : low] of some value. If low is not given,
  represents just [high] (only 1 bit), which is the same as [high : high].
  """
  if low is None:
    low = high
  return slice(low, high + 1)


def byte_count(bits):
  return bits // 8 + (0 if bits % 8 == 0 else 1)


def data_pack_directive(bits):
  if bits == 32:
    return "<I"
  elif bits == 64:
    return "<Q"
  else:
    raise ValueError("No data pack directive for size: {}".format(bits))
