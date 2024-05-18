


import struct



magic_number = ['BEBAFECA','DEADBEEF','ABAD1DEA','FEE1DEAD', 'BEEFDEAD',
                'C0FFEEC0', 'CAFEBABE', 'CAFED00D', 'D15EA5E0', 'DABBAD00', 'DABDAB00', 'D00DF00D',
                'D00DCAFE', 'D00DC0DE', 'D00DDEAD', 'D00DFACE', 'D00DF00D', 'D00DAB1E', 'D00D1E5E',
                'D00D1E55', 'D00D1E57', '0BADCAFE',]

# track closest float value to zero
closest_to_zero = float('inf')

for magic in magic_number:
    # bits
    bit_string = bin(int(magic, 16))[2:]

    bytes_value = bytes.fromhex(magic)
    float_value = struct.unpack('f', bytes_value)[0]
    closest_to_zero = min(closest_to_zero, abs(float_value))

    print(f"Magic Number: {magic} \t-> Float Value: {float_value} \t\t-> bits: {bit_string}")

print(f"\nClosest to zero: {closest_to_zero}")
