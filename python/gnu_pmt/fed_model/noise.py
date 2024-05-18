# this is a aux file for adding noise to the weights of a model
# it is called to simulte noise in the (32-bit floating point) mantissa to and from the server and clients

import warnings
import numpy as np

# make a function to add noise to the mantissa of a np.float32
def add_binary_noise(y:np.float32, noise:int) -> np.float32:
    '''add noise to the mantissa of a np.float32'''
    y_bin = y.view(np.int32) # get the bitwise representation
    if noise > 23:
        warnings.warn('noise should be less than 23 bits (the length of the mantissa) to avoid flipping the exponent bits or sign bit') 
    # give a random mask of 1s and 0s the length of the noise
    r_mask = np.random.randint(0, 2, noise)
    mask = 0
    for bit in r_mask:
        mask = (mask << 1) | bit
    
    y_new_bin = y_bin ^ mask # flip the lsb of the mantissa
    y_new = y_new_bin.view(np.float32) # convert back to np.float32
    return y_new

# make a function that will add noise to arrays of np.float32
def add_noise_to_array(arr:np.ndarray, noise:int) -> np.ndarray:
    '''add noise to an array of np.float32'''
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