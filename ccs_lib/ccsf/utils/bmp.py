import zlib, struct, time
from .PyBinaryReader.binary_reader import *
from array import array
from itertools import chain

def I8toBMP(width, height, indices, color_table):
    pixels = [color_table[i] for i in indices]
    pixels = bytes(chain.from_iterable(pixels))

    with BinaryReader(bytearray(), Endian.LITTLE, 'cp932') as br:
        #file header
        br.write_str("BM") #signature
        br.write_uint32(54 + len(pixels)) #file size
        br.write_uint16(0) #reserved 1
        br.write_uint16(0) #reserved 2
        br.write_uint32(54) #offset to pixel data
        #DIB header
        br.write_uint32(40) #DIB header size
        br.write_uint32(width) #width
        br.write_uint32(height) #height
        br.write_uint16(1) #color planes
        br.write_uint16(32) #bits per pixel
        br.write_uint32(0) #compression
        br.write_uint32(len(pixels)) #image size
        br.write_uint32(0) #horizontal resolution
        br.write_uint32(0) #vertical resolution
        br.write_uint32(0) #colors in color table
        br.write_uint32(0) #important colors
        #pixel data
        br.write_bytes(pixels)

        return br.buffer()

def I4toBMP(width, height, indices, color_table):
    
    #4 bit indexed
    pixels = [(color_table[i & 0xF] + color_table[i >> 4]) for i in indices]
    pixels = bytes(chain.from_iterable(pixels))

    with BinaryReader(bytearray(), Endian.LITTLE, 'cp932') as br:
        br.write_str("BM")
        br.write_uint32(54 + (width * height * 4))
        br.write_uint16(0)
        br.write_uint16(0)
        br.write_uint32(54)
        br.write_uint32(40)
        br.write_uint32(width)
        br.write_uint32(height)
        br.write_uint16(1)
        br.write_uint16(32)
        br.write_uint32(0)
        br.write_uint32(0)
        br.write_uint32(0)
        br.write_uint32(0)
        br.write_uint32(0)
        br.write_uint32(0)
        br.write_bytes(pixels)

        return br.buffer()