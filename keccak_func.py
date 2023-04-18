'''
Checking out the 256-bit Keccak hashing function

* test data encoded in UTF-8
* only for data that is of integer length of bytes (i.e. 1, 2, 3, 4...)
'''
import numpy as np
import os
from pathlib import Path

KECCAK_BYTES = 200
KECCAK_LANES = 25
KECCAK_PLANES_SLICES = 5

def Keccak_subfuncs(state):
    '''
    uint64 which gives us 64 bits per 1 "width" which *25 = 1600 bit state array
    
    F-order (which is also "Fortran order") implements 2D array as [X][Y] positions
    C-order implements 2D array as [Y][X] array of positions
    '''
    # orig code
    # state = np.copy(np.frombuffer(state, dtype=np.uint64, count=25))#.reshape([5, 5], order='F'))
    
    state_arr = np.ndarray((5,5), dtype=np.uint64, buffer=state, order='C')

    # === Printing data ===
    # print(state_arr)
    # # print(state_arr[0][0])
    # bytes_val = state_arr[0][0].tobytes()
    # print(bytes_val)
    
    # === Theta function ===
    # even out left and right columns
    leftShift = state_arr << 1 | state_arr >> 63
    rightShift = state_arr >> 1 | state_arr << 63
    
    # flatten columns - because each bit uses whole y-dimension
    leftFlat = np.zeros((5), dtype=np.uint64)
    rightFlat = np.zeros((5), dtype=np.uint64)
    
    for y in range(KECCAK_PLANES_SLICES):
        leftFlat ^= leftShift[y]
        rightFlat ^= rightShift[y]
        
    # XOR columns depending on their position
    columnsXORed = np.zeros_like(leftFlat)
    for x in range(KECCAK_PLANES_SLICES):
        columnsXORed[x] = leftFlat[(x-1)%5] ^ rightFlat[(x+1)%5]
    
    # XOR each bit with calculated columns
    for x in range(KECCAK_PLANES_SLICES):
        for y in range(KECCAK_PLANES_SLICES):
            state_arr[y][x] ^= columnsXORed[x]
    

def Keccak_256(inputBytes):
    rate = (1600-256*2)//8
    capacity = 1600//8 - rate
    inputB = bytearray(inputBytes)
    # 200 bytes == 1600 bit state
    
    state_str = bytearray([0 for i in range(200)])
    
    # == Absorb data (for now, small input)==
    for byte, it in zip(inputBytes, range(len(state_str)-rate)):
        # print(it, chr(byte))
        state_str[it] = byte
    
    # print(state_arr)
    
    len_diff = len(state_str) - capacity - len(inputBytes)
    # == Adding PAD to the chunk of data ==
    inputOffset = len(inputBytes)
    
    # print(len_diff)
    if len_diff > 0:
        if len_diff == 1:
            state_str[len(inputBytes)] = 0x81
        for it in range(len_diff):
            if it == 0:
                state_str[inputOffset] = 0x80
                continue
            if it == len_diff-1:
                state_str[inputOffset+it] = 0x01
                continue
            # state_arr[inputOffset+it] = 0x00
            
    Keccak_subfuncs(state_str)

with open('test_files/test.txt', 'rb') as input_to_hash:
    Keccak_256(input_to_hash.read())