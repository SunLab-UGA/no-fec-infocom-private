import math

def create_bit_position_dict(num_floats=3):
    bit_dict = {}
    float_labels = ["sign", "exponent", "significand"]
    float_components = [1, 8, 23]  # Number of bits in each component
    
    bit_position = 0
    for float_idx in range(1, num_floats+1):  # floats per symbol
        for component_idx, component_size in enumerate(float_components):
            label = float_labels[component_idx]
            for bit in range(1, component_size + 1):
                key = bit_position
                value = f"{label}-{bit}-{float_idx}"
                bit_dict[key] = value
                bit_position += 1
    
    return bit_dict

def min_steps_to_poles(length, poles):
    distances = []
    for i in range(length):
        min_distance = min(abs(i - pole) for pole in poles)
        distances.append(min_distance)
    # round up to nearest integer
    int_distances = [math.ceil(distance) for distance in distances]
    return distances, int_distances

def add_from_center(array, poles):
    length = len(array)
    for i in range(length):
        if i < poles[0] or i > poles[-1]:
            array[i] += 4
        elif (poles[0] <= i < poles[1]) or (poles[2] < i <= poles[3]):
            array[i] += 2
    
    return array

def reorder_by_priority(bit_array: list):
    '''reorganize the array by msb priority'''
    num_floats = len(bit_array)//32
    sub_arrays = [bit_array[i * 32:(i + 1) * 32] for i in range(num_floats)]
    reordered_array = []
    for ii in range(32):
        for jj in range(num_floats):
            reordered_array.append(sub_arrays[jj][ii])
    return reordered_array
# =================================================================================================

# assume a full frame with 96 coded bits and 4 pilot positions
n_bps = 2  # Number of bits per symbol (BPSK=1, QPSK=2, 16-QAM=4, 64-QAM=6)
n_cbps = 96  # Number of coded bits per OFDM symbol (BPSK=48 ,QPSK=96, 16-QAM=192, 64-QAM=288)
pilot_positions = [5, 19, 33, 47]  # Given pilot positions
# in_bits = [f'{i:02d}' for i in range(0,n_cbps)]
in_bits = [i for i in range(n_cbps)]

print("Pilot positions: ", pilot_positions)
print("Input bits: ", in_bits)

# Create the dictionary
# bit_position_dict = create_bit_position_dict(num_floats=n_cbps//32)

# # Print the dictionary
# for key in sorted(bit_position_dict.keys()):
#     print(f"{key}: {bit_position_dict[key]}",end=", ")
#     if key % 8 == 0 and key != 0:
#         print()
# print()


# Define the length of the list and the positions of the poles
length = 48*n_bps
base_poles = [4, 17, 30, 43]  # Poles located between the given indices
poles = [pole*n_bps+0.5 for pole in base_poles]  # Convert to bit positions
# add distance from the center
# center = length/2
# print("Center: ", center)
print("Poles: ", poles)
# Generate the list of minimum steps to the nearest pole
_,interleave_matrix = min_steps_to_poles(length, poles)

# add 2 to the outside, 1 to the inner and 0 to the middle
interleave_matrix = add_from_center(interleave_matrix, poles)
print("interleave matrix: ",interleave_matrix)

# copy the interleave matrix for the deinterleave operation
deint_matrix = interleave_matrix.copy()

# reorder the bits
bit_priority = reorder_by_priority(in_bits)
print("bit_priority: ", bit_priority)

# lastly, interleave the bits by taking the first priority bit 
# and placing it in the minimum of the min_steps_list
out_bits = [''] * len(in_bits)
for ii in range(len(in_bits)):
    # find the index with the min value within interleave_matrix and place the bit
    min_idx = interleave_matrix.index(min(interleave_matrix))
    # out_bits[min_idx] = bit_priority[ii]
    out_bits[min_idx] = in_bits[ii]
    interleave_matrix[min_idx] = 1000 # set the value to a high number to avoid reusing the index

# output the out_bits with a prepended 0 to make it 2 digits
_out_bits = [f'{i:02d}' for i in out_bits]
print("Output bits: ", _out_bits)
print("Output bits: ", out_bits)

# # show the reverse interleave operation
# deint = [''] * len(out_bits)
# for ii in range(len(out_bits)):
#     # find the index with the min value within interleave_matrix and place the bit
#     min_idx = deint_matrix.index(min(deint_matrix))
#     deint[min_idx] = out_bits[ii]
#     deint_matrix[min_idx] = 1000 # set the value to a high number to avoid reusing the index