from .ccsf.brccs import *
from .ccsf.ccs import *
from .ccsf.utils.PyBinaryReader.binary_reader import *
from .ccs_reader import read_ccs

def write_ccs(ccs: CCSFile):
    with BinaryReader(bytearray(), Endian.LITTLE, 'cp932') as br:
        '''brccs = BrCCSFile()
        brccs.Header = BrHeader()
        brccs.Header.filename = ccs.filename
        brccs.Header.version = ccs.version
        brccs.BrChunks = None
        brccs.StringTable = None'''
        br.write_struct(BrCCSFile(), ccs)
        return bytes(br.buffer())

