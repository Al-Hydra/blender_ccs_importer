import numpy as np
from .PyBinaryReader.binary_reader import *



def I8toBMP(width, height, indices, colorPalette):
    # Convert indices and colorPalette to NumPy arrays
    indices_array = np.array(indices, dtype=np.uint8)
    colorPalette_array = np.array(colorPalette, dtype=np.uint8)

    # Use indices_array as index to colorPalette_array
    pixels = colorPalette_array[indices_array]

    # Flatten pixels array and convert to bytes
    pixels_bytes = pixels.flatten().tobytes()

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
        br.write_bytes(pixels_bytes)

        return br.buffer()

def I4toBMP(width, height, indices, colorPalette):
    
    #4 bit indexed
    indices  = np.array(indices, dtype=np.uint8)
    colorPalette = np.array(colorPalette, dtype=np.uint8)

    # Use bitwise operations to extract lower and upper nibbles
    lower_nibble = indices & 0xF
    upper_nibble = indices >> 4

    #Create pixels array using NumPy array operations
    pixels = np.concatenate((colorPalette[lower_nibble], colorPalette[upper_nibble]), axis=1)

    # Flatten pixels array and convert to bytes
    pixels_bytes = pixels.flatten().tobytes()

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
        br.write_bytes(pixels_bytes)

        return br.buffer()