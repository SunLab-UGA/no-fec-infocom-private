import numpy as np

def compare_string_indices_divided(original_list, divisor):
    # Calculate the length of each segment
    segment_length = len(original_list) // divisor
    segments = [original_list[i * segment_length:(i + 1) * segment_length] for i in range(divisor)]
    print(f'segmented {segments}')
    # Check if the segments have the same string at any specific index
    for index in range(segment_length):
        # Collect elements at the current index from each segment if they are strings
        drops = [segment[index] for segment in segments if isinstance(segment[index], str)]
        success = [segment[index] for segment in segments if isinstance(segment[index], int)]
        print(f'drops: {drops}')
        print(f'success: {success}')
        # Check if all elements are the same and there's at least one element
        if len(drops) == divisor:
            print(f"Dropped packet at index: {index}")
        else:
            # give the first element which is not a string
            print(f"Success packet at index: {index} is {success[0]}")
            
# Example usage:
mixed_list = [1, "hello", 3, "world", "apple", "hello", 3, "world", 7, "apple", 2, "hello"]
print(f'rx {mixed_list}')
compare_string_indices_divided(mixed_list, 3)
print()

L = np.tile(mixed_list, 2)
print(f'rx {L}')