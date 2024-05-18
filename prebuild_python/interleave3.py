# clean up and refactor the interleave code

def interleave2(bits):
    """
    Interleave the bits according to the given priority matrix.
    
    :param bits: List of 96 bits representing the input.
    :return: List of 96 bits after interleaving.
    """
    if len(bits) != 96:
        raise ValueError("Input list must have exactly 96 elements.")
    
    priority_matrix = [
        80, 72, 64, 56, 48, 40, 32, 24, 16, 4, 10, 17, 25, 33, 41, 49, 57, 65, 73, 81, 88, 92, 93, 89, 82, 74, 66, 58, 50, 42, 34, 26, 18, 11, 5, 0, 2, 6, 12, 19, 27, 35, 43, 51, 59, 67, 75, 83, 84, 76, 68, 60, 52, 44, 36, 28, 20, 13, 7, 3, 1, 8, 14, 21, 29, 37, 45, 53, 61, 69, 77, 85, 90, 94, 95, 91, 86, 78, 70, 62, 54, 46, 38, 30, 22, 15, 9, 23, 31, 39, 47, 55, 63, 71, 79, 87
    ]
    
    # Initialize the interleaved_bits list with the same length as bits
    interleaved_bits = [0] * 96
    
    # Place the bits according to the priority matrix
    for i, priority in enumerate(priority_matrix):
        interleaved_bits[i] = bits[priority]
    
    return interleaved_bits

def reverse_interleave2(interleaved_bits):
    """
    Reverse the interleaving process to get the original bits.
    
    :param interleaved_bits: List of 96 bits after interleaving.
    :return: List of 96 bits representing the original input.
    """
    if len(interleaved_bits) != 96:
        raise ValueError("Input list must have exactly 96 elements.")
    
    priority_matrix = [
        80, 72, 64, 56, 48, 40, 32, 24, 16, 4, 10, 17, 25, 33, 41, 49, 57, 65, 73, 81, 88, 92, 93, 89, 82, 74, 66, 58, 50, 42, 34, 26, 18, 11, 5, 0, 2, 6, 12, 19, 27, 35, 43, 51, 59, 67, 75, 83, 84, 76, 68, 60, 52, 44, 36, 28, 20, 13, 7, 3, 1, 8, 14, 21, 29, 37, 45, 53, 61, 69, 77, 85, 90, 94, 95, 91, 86, 78, 70, 62, 54, 46, 38, 30, 22, 15, 9, 23, 31, 39, 47, 55, 63, 71, 79, 87
    ]
    
    # Initialize the original_bits list with the same length as interleaved_bits
    original_bits = [0] * 96
    
    # Reverse the interleaving process
    for i, priority in enumerate(priority_matrix):
        original_bits[priority] = interleaved_bits[i]
    
    return original_bits

def interleave(bits: list) -> list:
    '''reorder the bits by msb priority'''
    num_floats = len(bits)//32
    sub_arrays = [bits[i * 32:(i + 1) * 32] for i in range(num_floats)]
    reordered_array = []
    for ii in range(32):
        for jj in range(num_floats):
            reordered_array.append(sub_arrays[jj][ii])
    return reordered_array

def deinterleave(prioritized_bits: list) -> list:
    '''return the bits into consecutive 32bit float order'''
    num_floats = len(prioritized_bits)//32
    sub_arrays = [prioritized_bits[i * 3:(i + 1) * 3] for i in range(32)]
    reordered_array = []
    for ii in range(num_floats):
        for jj in range(32):
            reordered_array.append(sub_arrays[jj][ii])
    return reordered_array

# =================================================================================================

n_cbps = 96  # Number of coded bits per OFDM symbol (BPSK=48 ,QPSK=96, 16-QAM=192, 64-QAM=288)

# input_bits = [1 if i % 2 == 0 else 0 for i in range(96)]  # Example input bits
input_bits = [i for i in range(n_cbps)]
# first interleave the bits significance priority
sig_bits = interleave(input_bits)
# then interleave with placement priority
interleaved_bits = interleave2(sig_bits)
# deinterleave the bits
reversed_bits = reverse_interleave2(interleaved_bits)
# undo the significance priority
out_bits = deinterleave(reversed_bits)

print("Input Bits:      ", input_bits)
print("Significance Bits:", sig_bits)
print("Interleaved Bits:", interleaved_bits)
print("Reversed Bits:   ", reversed_bits)
print("Output Bits:     ", out_bits)
print("Is Reversed Correct?", input_bits == out_bits)

# =================================================================================================