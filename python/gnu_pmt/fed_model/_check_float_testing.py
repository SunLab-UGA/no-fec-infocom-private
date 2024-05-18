import numpy as np
# set the random seed
# np.random.seed(255)

# x = np.float32(1.0)


# # make a function that breaks the float32 bitwise into sign, exponent, and mantissa
# def float32_decompose(x):
#     # sign bit
#     sign = x >> 31
#     # exponent
#     exponent = (x >> 23) & 0xFF
#     # mantissa
#     mantissa = x & 0x7FFFFF
#     return sign, exponent, mantissa

# sign, exponent, mantissa = float32_decompose(x.view(np.int32))

# print(f'x: {x}')
# print(f'sign: {sign}')
# print(f'sign_bin: {sign:01b}')
# print(f'exponent: {exponent}')
# print(f'exponent_bin: {exponent:08b}')
# print(f'mantissa: {mantissa}')
# print(f'mantissa_bin: {mantissa:023b}')
# print()
# print(f'x: {x} == {sign} * 2^{exponent-127} * 1.{mantissa:023b}')

# # randomly flip the mantissa lsb to see the effect on the float
# mantissa = mantissa ^ 1 # flip the lsb
# print(f'mantissa: {mantissa}')
# print(f'x: {x} == {sign} * 2^{exponent-127} * 1.{mantissa:023b}')

# # recombine the float32 bitwise representation
# def float32_recompose(sign, exponent, mantissa):
#     return (sign << 31) | (exponent << 23) | mantissa

# x_new = float32_recompose(sign, exponent, mantissa)
# print(f'x_new: {x_new}')

# =============================================================================

# noise = 23 # mantissa noise (up to 23 bits)
# # give a random mask of 1s and 0s the length of the noise
# r_mask = np.random.randint(0, 2, noise)
# print(f'r_mask: {r_mask}')

# mask = 0
# for bit in r_mask:
#     mask = (mask << 1) | bit
# print(f'mask: {mask}')
# print(f'mask: {mask:b}')

# y = np.float32(1.0)
# y_bin = y.view(np.int32)
# print(f'y: {y}')
# print(f'y_bin: {y_bin:b}')

# # flip the lsb of the mantissa
# y_new_bin = y_bin ^ mask
# print(f'y_new_bin: {y_new_bin:b}')
# y_new = y_new_bin.view(np.float32)
# print(f'y_new: {y_new}')

# =============================================================================

# make a function to add noise to the mantissa of a np.float32
def add_binary_noise(y:np.float32, noise:int) -> np.float32:
    '''add noise to the mantissa of a np.float32'''
    y_bin = y.view(np.int32) # get the bitwise representation
    if noise > 23:
        raise Warning('noise should be less than 23 bits (the length of the mantissa) to avoid flipping the exponent bits or sign bit') 
    # give a random mask of 1s and 0s the length of the noise
    r_mask = np.random.randint(0, 2, noise)
    print(f'r_mask: {r_mask}') if False else None
    mask = 0
    for bit in r_mask:
        mask = (mask << 1) | bit
    
    y_new_bin = y_bin ^ mask # flip the lsb of the mantissa
    y_new = y_new_bin.view(np.float32) # convert back to np.float32
    return y_new

# make a function that will add noise to arrays of np.float32
def add_noise_to_array(arr:np.ndarray, noise:int) -> np.ndarray:
    '''add noise to arrays of np.float32'''
    return np.array([add_binary_noise(x, noise) for x in arr])

def add_noise_to_array_v2(arr:np.ndarray, noise:int, percent:float) -> np.ndarray:
    '''add noise to arrays of np.float32
    add noise to a percentage of the array'''
    arr_len = len(arr)
    noise_coeff = np.random.choice([0, 1], arr_len, p=[1-percent, percent])
    print(f'{noise_coeff=}')
    out = []
    for i,x in enumerate(arr):
        print(f'{i=}, {x=}, {noise_coeff[i]=}')
        if noise_coeff[i] == 1:
            print(f'adding noise to {x}')
            out.append(add_binary_noise(x, noise))
        else:
            print(f'not adding noise to {x}')
            out.append(x)
    return np.array(out)


    # return np.array([add_binary_noise(x, noise) for i,x in enumerate(arr) if noise_coeff[i] == 1 else noise_coeff[i] == 0])

# test the function
noise = 23 # mantissa noise (up to 23 bits)
x = np.array([1.0, -20.0, 300.0], dtype=np.float32)
print(f'x: {x}')
x_noisy = add_noise_to_array(x, noise)
print(f'x_noisy: {x_noisy}')

print()

# test the function 2
pn = 0.5 # probability of noise added to the array
x = np.array([1.0, -20.0, 300.0], dtype=np.float32)
print(f'x: {x}')
x_noisy = add_noise_to_array_v2(x, noise, pn)
print(f'x_noisy: {x_noisy}')

