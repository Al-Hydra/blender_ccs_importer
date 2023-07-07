import json
from time import perf_counter
from .ccsf.brccs import BrCCSFile, CCSTypes
from .ccsf.ccs import *
from .ccsf.utils.PyBinaryReader.binary_reader import *

def read_ccs(file):
    start = perf_counter()
    with open(file, 'rb') as f:
        file_bytes = f.read()

    with BinaryReader(file_bytes, Endian.LITTLE, 'cp932') as br:
        #start = perf_counter()
        ccs_file: BrCCSFile = br.read_struct(BrCCSFile)
        #print(f'CCS read time: {perf_counter() - start}')

    table = ccs_file.ChunkRefs
    CCSChunks = ChunksDict(ccs_file.BrChunks, table)
    
    ccs: CCSFile = CCSFile(ccs_file.Header.FileName, ccs_file.Header.Version, table.Paths, table.Names, CCSChunks)
    print(f'ccs file was read in {perf_counter() - start}')

    
    return ccs