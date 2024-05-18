# interleave testing and examples

import math

def calculate_first_permutation(n_cbps, pilot_spacing):
    s = max(n_cbps // 2, 1)

    sign_exponent_indices = []
    significand_indices = []

    # Separate indices for sign + exponent and significand
    for j in range(n_cbps):
        float_idx = j // 32       # Which float
        bit_idx = j % 32          # Bit within the float
        if bit_idx < 9:           # Sign and exponent bits
            sign_exponent_indices.append(j)
        else:                     # Significand bits
            significand_indices.append(j)
    
    first = [-1] * n_cbps

    # Map sign + exponent indices near pilot symbols
    for i in range(len(sign_exponent_indices)):
        first[i] = (i // 9) * pilot_spacing + (i % 9)
    
    # Fill the rest with significand indices
    for i in range(len(significand_indices)):
        first[len(sign_exponent_indices) + i] = significand_indices[i]
    
    return first

def calculate_second_permutation(n_cbps):
    second = [0] * n_cbps
    for i in range(n_cbps):
        second[i] = 16 * i - (n_cbps - 1) * (16 * i // n_cbps)
        second[i] %= n_cbps  # Ensure indices are within range
    return second

def interleave(in_bits, frame_n_sym, n_cbps, pilot_spacing, reverse=False):
    first = calculate_first_permutation(n_cbps, pilot_spacing)
    second = calculate_second_permutation(n_cbps)
    
    out_bits = [''] * len(in_bits)
    
    for i in range(frame_n_sym):
        for k in range(n_cbps):
            if reverse:
                out_bits[i * n_cbps + second[first[k]]] = in_bits[i * n_cbps + k]
            else:
                out_bits[i * n_cbps + k] = in_bits[i * n_cbps + second[first[k]]]
    
    return out_bits

# Example usage
n_cbps = 96  # Number of coded bits per OFDM symbol
frame_n_sym = 1  # Number of symbols in the frame (for simplicity)
pilot_spacing = 16  # Example spacing of pilot symbols
in_bits = [f'{i:02d}' for i in range(n_cbps)]  # Example input bits: ['00', '01', '02', ..., '95']

# Interleave
out_bits = interleave(in_bits, frame_n_sym, n_cbps, pilot_spacing, reverse=False)

# Print results
print("Input bits: ", in_bits)
print("Interleaved bits: ", out_bits)
print("Deinterleaved bits: ", interleave(out_bits, frame_n_sym, n_cbps, pilot_spacing, reverse=True))

pilots = [-21, -7 , 7 , 21] # of 52 subcarriers
# shift the indices of the pilot symbols reflect a 0 based index
pilots = [x + 26 for x in pilots] # 52/2 = 26
print(pilots)

