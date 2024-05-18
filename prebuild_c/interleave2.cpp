#include <iostream>
#include <vector>
#include <stdexcept>
#include <algorithm>
#include <cmath>

const int MAX_BITS_PER_SYM = 288;

// Function to reverse bits in a byte
unsigned char reverse_bits(unsigned char byte) {
    byte = (byte & 0xF0) >> 4 | (byte & 0x0F) << 4;
    byte = (byte & 0xCC) >> 2 | (byte & 0x33) << 2;
    byte = (byte & 0xAA) >> 1 | (byte & 0x55) << 1;
    return byte;
}

void print_bits(const char* data_bits, int size) {
    for (int i = 0; i < size; i++) {
        std::cout << static_cast<int>(data_bits[i]);
        std::cout << " ";

    }std::cout << std::endl;
}
#define MAX_BITS_PER_SYM 288
void interleave(const char* in, char* out, bool reverse)
{
    int psdu_size = 1500; // Maximum size of a packet
    const int n_dbps = 96; // Number of data bits per OFDM symbol (QPSK)
    int n_sym = (int)ceil((16 + 8 * psdu_size + 6) / (double)n_dbps);
    std::cout << "n_sym: " << n_sym << std::endl;
    int n_data_bits = n_sym * n_dbps;  // total number of data bits, including service and padding
    const int n_cbps = 96; // Number of coded bits per OFDM symbol
    int num_floats = n_cbps / 32;
    int n_bytes = 1530; // 4*375+2+4+24
    if (n_cbps != 96) { //only valid for QPSK
        throw std::invalid_argument("Input array must have exactly 96 elements.");
    }

    std::vector<int> priority_matrix = {
        80, 72, 64, 56, 48, 40, 32, 24, 16, 4, 10, 17, 25, 33, 41, 49, 57, 65, 73, 81, 88, 92, 93, 89, 82, 74, 66, 58, 50, 42, 34, 26, 18, 11, 5, 0, 2, 6, 12, 19, 27, 35, 43, 51, 59, 67, 75, 83, 84, 76, 68, 60, 52, 44, 36, 28, 20, 13, 7, 3, 1, 8, 14, 21, 29, 37, 45, 53, 61, 69, 77, 85, 90, 94, 95, 91, 86, 78, 70, 62, 54, 46, 38, 30, 22, 15, 9, 23, 31, 39, 47, 55, 63, 71, 79, 87
    };
    // place the last 2 bytes behind the signal field (2 bytes) to align with the 32 bit boundaries
    char* square_bits = (char*)calloc(n_data_bits, sizeof(char));
    int step_in_bits[MAX_BITS_PER_SYM]; //temp storage per symbol interleaving
    int step_out_bits[MAX_BITS_PER_SYM]; //temp storage per symbol interleaving
    
    // temp storage for the bits after the first interleaving/deinterleaving
    std::vector<char> step_bits(n_cbps);

    if (reverse) { // deinterleave
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
    } else { // interleave ==================================================
        // byte shift to align with 32 bit boundaries (packet wide)
        square_bits[0] = in[0]; square_bits[1] = in[1]; //service bits
        square_bits[2] = reverse_bits(in[n_bytes-2]);
        square_bits[3] = reverse_bits(in[n_bytes-1]); //last half of crc bits, reverse to be consistent

        for (int i = 4; i < n_bytes-2; i+=1) { //fill the rest
            square_bits[i] = reverse_bits(in[i-2]); 
        }

        // DEBUG
        std::cout << "flipped Bits:      " << std::endl;
        for (int i = 0; i < 1526; ++i) {
            std::cout << static_cast<int>(square_bits[i]) << " ";
            if (i % 16 == 15) {
                std::cout << std::endl;
            }
        }std::cout << std::endl;


        //first interleaving (bit priority)
        for (int k = 0; k < n_sym; ++k) { // number of symbols
            // place the first packet in step_bits
            for (int i = 0; i < n_cbps; ++i) {
                step_in_bits[i] = square_bits[i + k * n_cbps];
            }

            std::cout << "step_in_bits: " << std::endl;
            print_bits(step_in_bits, n_cbps);

            // Perform the interleaving with bit priority
            for (int i = 0; i < num_floats; ++i) { // floats per symbol per packet
                for (int j = 0; j < 32; ++j) { // bits per float per symbol
                    step_out_bits[j * num_floats + i] = step_in_bits[i * 32 + j];
                }            
            }

            std::cout << "step_out_bits: " << std::endl;
            print_bits(step_out_bits, n_cbps);

            // place the interleaved packet in square_bits
            for (int i = 0; i < n_cbps; ++i) {
                square_bits[i + k * n_cbps] = step_out_bits[i];
            }
        }

        //second interleaving (placement priority)
        for (int k = 0; k < n_sym; ++k) { // number of symbols
            // place the first packet in step_bits
            for (int i = 0; i < n_cbps; ++i) {
                step_in_bits[i] = square_bits[i + k * n_cbps];
            }
            // Perform the interleaving with placement priority
            for (int i = 0; i < n_cbps; ++i) {
                step_out_bits[i] = step_in_bits[priority_matrix[i]];
            }
            // place the interleaved packet in square_bits
            for (int i = 0; i < n_cbps; ++i) {
                square_bits[i + k * n_cbps] = step_out_bits[i];
            }
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
    for (int i = 0; i < 1530; ++i) {
        std::cout << static_cast<int>(input_bits[i]) << " ";
        if (i % 12 == 11) {
            std::cout << std::endl;
        }
    }std::cout << std::endl;

    // Interleave the bits
    interleave(input_bits, output_bits, false);
    std::cout << "Interleaved Bits: " << std::endl;
    for (int i = 0; i < 1530; ++i) {
        std::cout << static_cast<int>(input_bits[i]) << " ";
        if (i % 12 == 11) {
            std::cout << std::endl;
        }
    }std::cout << std::endl;

    // Reverse the interleaving
    //interleave(output_bits, reversed_bits, true);
    // std::cout << "\nReversed Bits:   ";
    // for (int i = 0; i < n_cbps; ++i) {
    //     std::cout << static_cast<int>(reversed_bits[i]) << " ";
    // }
    // std::cout << "\nIs Reversed Correct? " << (std::equal(input_bits, input_bits + n_cbps, reversed_bits) ? "true" : "false") << std::endl;

    return 0;
}


