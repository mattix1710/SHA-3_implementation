'''
    Naive implementation of Keccak function - SHA-3 hash function
'''
import binascii

# from .keccak_func import Keccak_256
import FIPS_numpy
import keccak_func

with open('test_files/test.txt', 'rb') as input_to_hash:
    # Keccak_256(input_to_hash.read())
    b = bytearray(input_to_hash.read())
    # r, c, s, n = 1088, 512, 0x1F, 528
    # h = FIPS_numpy.Keccak(r, c, b, s, n//8)
    print("FIPS:", binascii.hexlify(FIPS_numpy.SHA3_256(b)))
    print("")
    print("OURS:", binascii.hexlify(keccak_func.Keccak_256(b)))