#include <iostream>
#include <vector>
#include <stdexcept>
#include <algorithm>

const int MAX_BITS_PER_SYM = 288;

// Function to reverse bits in a byte
unsigned char reverse_bits(unsigned char byte) {
    byte = (byte & 0xF0) >> 4 | (byte & 0x0F) << 4;
    byte = (byte & 0xCC) >> 2 | (byte & 0x33) << 2;
    byte = (byte & 0xAA) >> 1 | (byte & 0x55) << 1;
    return byte;
}

void interleave(const char* in, char* out, bool reverse)
{
    const int n_cbps = 96; // Number of coded bits per OFDM symbol
    int num_floats = n_cbps / 32;
    int n_bytes = 1526; // 4*375+2+4+24
    if (n_cbps != 96) { //only valid for QPSK
        throw std::invalid_argument("Input array must have exactly 96 elements.");
    }

    std::vector<int> priority_matrix = {
        80, 72, 64, 56, 48, 40, 32, 24, 16, 4, 10, 17, 25, 33, 41, 49, 57, 65, 73, 81, 88, 92, 93, 89, 82, 74, 66, 58, 50, 42, 34, 26, 18, 11, 5, 0, 2, 6, 12, 19, 27, 35, 43, 51, 59, 67, 75, 83, 84, 76, 68, 60, 52, 44, 36, 28, 20, 13, 7, 3, 1, 8, 14, 21, 29, 37, 45, 53, 61, 69, 77, 85, 90, 94, 95, 91, 86, 78, 70, 62, 54, 46, 38, 30, 22, 15, 9, 23, 31, 39, 47, 55, 63, 71, 79, 87
    };
    // place the last 2 bytes behind the signal field (2 bytes) to align with the 32 bit boundaries
    std::vector<char> square_bits(n_cbps); 
    // temp storage for the bits after the first interleaving/deinterleaving
    std::vector<char> step_bits(n_cbps);

    if (reverse) {
        // Perform reverse interleaving
        for (int i = 0; i < n_cbps; ++i) {
            step_bits[priority_matrix[i]] = in[i];
        }

        // Undo the significance priority
        for (int i = 0; i < num_floats; ++i) {
            for (int j = 0; j < 32; ++j) {
                out[i * 32 + j] = step_bits[j * num_floats + i];
            }
        }
    } else {
        // shift the input bits to the left by 2 bytes (remove the service bits)
        for (int i = 0; i < 1528; i+=1) {
            step_bits[i] = reverse_bits(in[i+2]); 
        }

        // Perform the significance priority interleaving
        for (int i = 0; i < num_floats; ++i) {
            for (int j = 0; j < 32; ++j) {
                step_bits[j * num_floats + i] = input_bits_ptr[i * 32 + j];
            }
        }
        // Perform the interleaving with placement priority
        for (int i = 0; i < n_cbps; ++i) {
            out[i] = step_bits[priority_matrix[i]];
        }
    }
}

int main() {
    
    
    const int n_cbps = 96;
    char input_bits[4*375+2+4+24]; // 4*375+2+4+24 = 1530 bytes, the maximum size of a packet
    int n_bytes =
    // fill the input bits
    // 00000000 00000000 00010000 00000000 00000000 00000000 00001100 00101000 01010010 01100111 01100010 00100111 01001000 00101100 01101010 00011110 00001001 11010101 01000010 01000010 01000010 01000010 01000010 01000010 00000000 00000000
    input_bits[0] = 0b00000000; //service
    input_bits[1] = 0b00000000; //service
    input_bits[2] = 0b00010000; input_bits[3] = 0b00000000; input_bits[4] = 0b00000000; input_bits[5] = 0b00000000;
    input_bits[6] = 0b00001100; input_bits[7] = 0b00101000; input_bits[8] = 0b01010010; input_bits[9] = 0b01100111;
    input_bits[10] = 0b01100010; input_bits[11] = 0b00100111; input_bits[12] = 0b01001000; input_bits[13] = 0b00101100;
    input_bits[14] = 0b01101010; input_bits[15] = 0b00011110; input_bits[16] = 0b00001001; input_bits[17] = 0b11010101;
    input_bits[18] = 0b01000010; input_bits[19] = 0b01000010; input_bits[20] = 0b01000010; input_bits[21] = 0b01000010;
    input_bits[22] = 0b01000010; input_bits[23] = 0b01000010; input_bits[24] = 0b00000000; input_bits[25] = 0b00000000;
    //fill the rest with 00001110 10000110 10101110 00110110
    for (int i = 26; i < 1526; i+=4) {
        input_bits[i] = 0b00001110; input_bits[i+1] = 0b10000110; input_bits[i+2] = 0b10101110; input_bits[i+3] = 0b00110110;
    }
    //make the last a real crc 11010100 11101011 00010100 00011101
    input_bits[1526] = 0b11010100; input_bits[1527] = 0b11101011; input_bits[1528] = 0b00010100; input_bits[1529] = 0b00011101;

    char output_bits[n_cbps];
    char reversed_bits[n_cbps];
    // Output the results
    std::cout << "Input Bits:      " << std::endl;
    for (int i = 0; i < 1526; ++i) {
        std::cout << static_cast<int>(input_bits[i]) << " ";
        if (i % 16 == 15) {
            std::cout << std::endl;
        }
    }std::cout << std::endl;

    // create a new pointer which is past the first 2 bytes
    char* input_bits_ptr = input_bits + 2;

    //flip all bytes from big endian to little endian
    for (int i = 0; i < 1528; i+=1) {
        input_bits_ptr[i] = reverse_bits(input_bits_ptr[i]);
    }

    std::cout << "flipped Bits:      " << std::endl;
    for (int i = 0; i < 1526; ++i) {
        std::cout << static_cast<int>(input_bits_ptr[i]) << " ";
        if (i % 16 == 15) {
            std::cout << std::endl;
        }
    }std::cout << std::endl;

    // Interleave the bits
    interleave(input_bits_ptr, output_bits, false);
    std::cout << "\nInterleaved Bits: ";
    for (int i = 0; i < n_cbps; ++i) {
        std::cout << static_cast<int>(output_bits[i]) << " ";
    }

    // Reverse the interleaving
    interleave(output_bits, reversed_bits, true);
    std::cout << "\nReversed Bits:   ";
    for (int i = 0; i < n_cbps; ++i) {
        std::cout << static_cast<int>(reversed_bits[i]) << " ";
    }
    std::cout << "\nIs Reversed Correct? " << (std::equal(input_bits, input_bits + n_cbps, reversed_bits) ? "true" : "false") << std::endl;

    return 0;
}


