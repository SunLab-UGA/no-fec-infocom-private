import struct
import numpy as np
def generate_floats_from_bits(start:int, count:int) -> list:
    '''generate a predefined bitwise sequence of floats starting from a given integer'''
    floats = []
    for i in range(start, start + count):
        # Pack the integer as a 32-bit unsigned integer, then unpack it as a float
        floats.append(struct.unpack('f', struct.pack('<I', i))[0])
    return floats

def generate_floats_from_bits_np(start:int, count:int) -> np.array:
    '''generate a predefined bitwise sequence of floats starting from a given integer'''
    floats = np.zeros(count-start, dtype=np.float32)
    for i in range(start, start + count):
        # Pack the integer as a 32-bit unsigned integer, then unpack it as a float
        floats[i-start] = struct.unpack('f', struct.pack('<I', i))[0]
    return floats

def check_preamble(sequence:np.array, packet:np.array, valid_limit:int=10) -> int|None:
    '''check if a preamble sequence is present in an array of recievied floats
    if the preamble packet contains X valid limit of a float in the sequence, 
    return where in the sequence it was found
    ELSE return None'''
    # check if 32-bit float input
    if packet.dtype != np.float32:
        raise ValueError("Packet must be 32-bit floats")
    if sequence.dtype != np.float32:
        raise ValueError("Sequence must be 32-bit floats")
    # counts
    counts = np.zeros(len(sequence), dtype=int)
    for float_val in packet:
        for seq_idx, seq_float in enumerate(sequence):
            if float_val == seq_float:
                counts[seq_idx] += 1
                if counts[seq_idx] >= valid_limit:
                    return seq_idx
    return None

if __name__ == "__main__":
    # Example usage: Generate 10 floats starting from 0
    start = 0
    count = 10
    float_sequence = generate_floats_from_bits(start, count)
    print(float_sequence)

    float_sequence = generate_floats_from_bits_np(start, count)
    print(float_sequence)
