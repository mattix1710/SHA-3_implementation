'''
Checking out the 256-bit Keccak hashing function

* test data encoded in UTF-8
* only for data that is of integer length of bytes (i.e. 1, 2, 3, 4...)
'''
import numpy as np
import os
from pathlib import Path
import binascii

KECCAK_BYTES = 200
KECCAK_LANES = 25
KECCAK_PLANES_SLICES = 5

# all Rho shifts that are %64 in order to match the overall shift
RHO_SHIFTS = np.array([[0, 36, 3, 41, 18],
                       [1, 44, 10, 45, 2],
                       [62, 6, 43, 15, 61],
                       [28, 55, 25, 21, 56],
                       [27, 20, 39, 8, 14]], dtype=np.uint64)

IOTA_ROUND_CONSTANTS = np.array([0x0000000000000001,0x0000000000008082, 0x800000000000808A,
                            0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
                            0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
                            0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
                            0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
                            0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
                            0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
                            0x8000000000008080, 0x0000000080000001, 0x8000000080008008],
                            dtype=np.uint64)

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
    
    for round in range(24):
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
                
        if round == 0:
            print("THETA", state_arr)
                
        # === Rho function ===
        # Rho shift of given z offset
        # move to the left and bitwise OR moved data and their new position
        # TODO: probably revise - change RHO_SHIFTS
        state_arr = state_arr << RHO_SHIFTS | state_arr >> np.uint64(64 - RHO_SHIFTS)
        
        # === Pi function ===
        # create auxilliary table
        # shuffle between x & y axes
        state = np.zeros_like(state_arr)
        for x in range(KECCAK_PLANES_SLICES):
            for y in range(KECCAK_PLANES_SLICES):
                state[y][x] = state_arr[x][(x+3*y)%5]
        state_arr = state
        
        # === Chi function ===
        # create auxilliary table
        # XOR each bit with XOR of negation of bit one position to the right and bit two positions to the right
        state = np.zeros_like(state_arr)
        for y in range(KECCAK_PLANES_SLICES):
            for x in range(KECCAK_PLANES_SLICES):
                state[y][x] = state_arr[y][x] ^ (~state_arr[y][(x+1)%5] & state_arr[y][(x+2)%5])
        state_arr = state
        
        # === Iota function ===
        # XOR first lane (with x, y coord as 0,0) with the round constant RC depending on the current round
        state_arr[0][0] ^= IOTA_ROUND_CONSTANTS[round]
        
    return bytearray(state_arr.tobytes(order='C'))

##########################
# TEMP test
##########################

THETA_REORDER = ((4, 0, 1, 2, 3), (1, 2, 3, 4, 0))

def Keccak_subfuncs_F_order(state):
    state_arr = np.ndarray((5,5), dtype=np.uint64, buffer=state, order='F')
    
    for round in range(24):
        # THETA - subfunction taken from FIPS_numpy.py/KeccakF1600
        array_shift = state_arr << 1 | state_arr >> 63
        state_arr ^= np.bitwise_xor.reduce(state_arr[THETA_REORDER[0], ], 1, keepdims=True) ^ np.bitwise_xor.reduce(array_shift[THETA_REORDER[1], ], 1, keepdims=True)
        
        # RHO
        state_arr = state_arr << RHO_SHIFTS | state_arr >> np.uint64(64-RHO_SHIFTS)
        
        # PI
        state = np. zeros_like(state_arr)
        for x in range(KECCAK_PLANES_SLICES):
            for y in range(KECCAK_PLANES_SLICES):
                state[x][y] = state_arr[(x+3*y)%5][x]
        state_arr = state
        
        # CHI
        state = np.zeros_like(state_arr)
        for x in range(KECCAK_PLANES_SLICES):
            for y in range(KECCAK_PLANES_SLICES):
                state[x][y] = state_arr[x][y] ^ (~state_arr[(x+1)%5][y] & state_arr[(x+2)%5][y])
        state_arr = state
        
        state_arr[0][0] ^= IOTA_ROUND_CONSTANTS[round]
        
    return bytearray(state_arr.tobytes(order='F'))

    
    

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
    
    # print("STATE:", state_str)
    
    len_diff = len(state_str) - capacity - len(inputBytes)
    # == Adding PAD to the chunk of data ==
    inputOffset = len(inputBytes)
    
    # print(len_diff)
    if len_diff > 0:
        if len_diff == 1:
            state_str[len(inputBytes)] = 0x81
        for it in range(len_diff):
            if it == 0:
                state_str[inputOffset] = 0x06#0x80
                continue
            if it == len_diff-1:
                state_str[inputOffset+it] = 0x80#0x01
                continue
            # state_arr[inputOffset+it] = 0x00
    # print("PADDING:", state_str[:rate])
            
    # state_str = Keccak_subfuncs(state_str)
    state_str = Keccak_subfuncs_F_order(state_str)
    
    # print("FUNC:", state_str)
    return state_str[:(256//8)]

    
    

with open('test_files/test.txt', 'rb') as input_to_hash:
    print(binascii.hexlify(Keccak_256(input_to_hash.read())))