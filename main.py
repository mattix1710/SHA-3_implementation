from .keccak_func import Keccak_256

with open('test_files/test.txt', 'rb') as input_to_hash:
    Keccak_256(input_to_hash.read())