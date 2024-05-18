#include <iostream>
#include <vector>
#include <cstring>  // For std::memcmp
#include <iomanip>

// Mock definitions (Assuming these are defined elsewhere)
struct frame_param {
    int n_sym;  // Number of symbols
};

struct ofdm_param {
    int n_cbps;  // Number of coded bits per OFDM symbol
};

// Helper function definitions from your code (assuming these are defined elsewhere)
void setBit(char* output, int n, bool value);
bool getBit(const char* input, int n);
void reorderBits(const char* input, char* output, const std::vector<int>& index_matrix);
unsigned char reverse_bits(unsigned char byte);

// Your provided function (assuming it is defined elsewhere)
void interleave2(char* in, char* out, frame_param& frame, ofdm_param& ofdm, bool reverse); //removed const

// Main function to run test cases
int main() {
    // Define parameters for the test
    ofdm_param ofdm = {96};  // n_cbps = 96 as given in your example
    frame_param frame = {25};  // 25 symbols for the test

    // Test input data: 25 symbols, 12 bytes per symbol (as per n_cbps = 96)
    char in[300];  // 25 symbols * 12 bytes per symbol
    char out[300];       // Output buffer to store the interleaved data
    char reversed[300];  // Buffer to store the reversed data

    // Fill input data with a repeating pattern
    for (int i = 0; i < 300; ++i) {
        in[i] = i % 256;  // Use a simple incremental pattern, wrapped around at 256
    }

    // Print the output bytes and verification result
    std::cout << "Original input bytes:" << std::endl;
    for (int i = 0; i < 300; i++) {
        std::cout << std::hex << (int)(unsigned char)in[i] << " ";
        if ((i + 1) % 12 == 0) std::cout << std::endl;  // New line per symbol for readability
    }

    // Perform interleaving
    interleave2(in, out, frame, ofdm, false);  // Forward interleaving

    std::cout << "Interleaved output bytes:" << std::endl;
    for (int i = 0; i < 300; i++) {
        std::cout << std::hex << (int)(unsigned char)out[i] << " ";
        if ((i + 1) % 12 == 0) std::cout << std::endl;  // New line per symbol for readability
    }

    // Perform reverse interleaving to attempt to recover the original input
    interleave2(out, reversed, frame, ofdm, true);  // Reverse interleaving

    std::cout << "Reversed output bytes:" << std::endl;
    for (int i = 0; i < 300; i++) {
        std::cout << std::hex << (int)(unsigned char)reversed[i] << " ";
        if ((i + 1) % 12 == 0) std::cout << std::endl;  // New line per symbol for readability
    }

    // Compare the original input with the reversed output
    bool is_identical = (std::memcmp(in, reversed, 300) == 0);

    std::cout << "Test result: " << (is_identical ? "PASSED" : "FAILED") << std::endl;

    return 0;
}

// Helper function to set the nth bit of a byte array
void setBit(char* output, int n, bool value) {
    if (value)
        output[n / 8] |= (1 << (7 - n % 8));
    else
        output[n / 8] &= ~(1 << (7 - n % 8));
}
// Helper function to get the nth bit of a byte array
bool getBit(const char* input, int n) {
    return (input[n / 8] & (1 << (7 - n % 8))) != 0;
}
// Function to reorder bits based on a index matrix
void reorderBits(const char* input, char* output, const std::vector<int>& index_matrix) {
    for (int i = 0; i < 96; ++i) {  // 96 bits in 12 bytes
        bool bitValue = getBit(input, i);
        setBit(output, index_matrix[i], bitValue);
    }
}
// Function to reverse bits in a byte
unsigned char reverse_bits(unsigned char byte) {
    byte = (byte & 0xF0) >> 4 | (byte & 0x0F) << 4;
    byte = (byte & 0xCC) >> 2 | (byte & 0x33) << 2;
    byte = (byte & 0xAA) >> 1 | (byte & 0x55) << 1;
    return byte;
}

// Interleave knowing the data is 32 bit floats (keep msb close to the pilot "poles")
void interleave2(char* in, char* out, frame_param& frame, ofdm_param& ofdm, bool reverse){ //removed const
    int n_cbps = ofdm.n_cbps; // number of coded bits per OFDM symbol
    int n_sym = frame.n_sym;
    std::cout << "n_cbps: " << n_cbps << std::endl;
    std::cout << "n_sym: " << n_sym << std::endl;

    // if (n_cbps != 96) {
    //     // use the normal interleave function
    //     std::cout << "Using normal interleave function!?" << std::endl;
    //     return interleave(in, out, frame, ofdm, reverse);
    // }
    // debugs
    std::cout << "Using special interleave function!" << std::endl;

    // Significance matrix, high significance bits get placed first
    std::vector<int> significance_matrix = {
        0, 32, 64, 1, 33, 65, 2, 34, 66, 3, 35, 67, 4, 36, 68, 5, 37, 69, 6, 38, 70, 7, 39, 71, 8, 40, 72, 9, 41, 73, 10, 42, 
        74, 11, 43, 75, 12, 44, 76, 13, 45, 77, 14, 46, 78, 15, 47, 79, 16, 48, 80, 17, 49, 81, 18, 50, 82, 19, 51, 83, 20, 52, 84, 21, 
        53, 85, 22, 54, 86, 23, 55, 87, 24, 56, 88, 25, 57, 89, 26, 58, 90, 27, 59, 91, 28, 60, 92, 29, 61, 93, 30, 62, 94, 31, 63, 95
        };
    // Priority matrix, high priority (significant) bits get placed near pilot symbols 
    std::vector<int> priority_matrix = {
        0, 32, 64, 1, 33, 65, 2, 34, 66, 3, 35, 67, 4, 36, 68, 5, 37, 69, 6, 38, 70, 7, 39, 71, 8, 40, 72, 9, 41, 73, 10, 42, 
        74, 11, 43, 75, 12, 44, 76, 13, 45, 77, 14, 46, 78, 15, 47, 79, 16, 48, 80, 17, 49, 81, 18, 50, 82, 19, 51, 83, 20, 52, 84, 21, 
        53, 85, 22, 54, 86, 23, 55, 87, 24, 56, 88, 25, 57, 89, 26, 58, 90, 27, 59, 91, 28, 60, 92, 29, 61, 93, 30, 62, 94, 31, 63, 95
    };
    char symbol_bytes[12] = {}; // holds each symbol from the input
    char step_in_bytes[12] = {}; // temp storage per symbol interleaving
    char step_out_bytes[12] = {}; // temp storage per symbol interleaving

    int n_bytes = n_sym*4*3;
    char square_bytes[n_bytes] = {}; // 4 bytes per 32 bit float, 3 floats per symbol

    if (!reverse){ // forward interleaving
        // byte shift to align with 32 bit boundaries (packet wide)
        int bytes_to_move = 2;
        int move_from_index  = 24;  // Start of the last two bytes in the 26-byte segment

        // Move the entire content up to the bytes to be moved
        std::memmove(square_bytes, in, move_from_index);
        // Shift the rest of the array left by two positions to fill the gap
        std::memmove(square_bytes + move_from_index, in + move_from_index + bytes_to_move, n_bytes - move_from_index - bytes_to_move);
        // Place the two moved bytes at the end of the total_size array
        std::memcpy(square_bytes + n_bytes - bytes_to_move, in + move_from_index, bytes_to_move);
        // for (int i = 0; i < n_bytes; i++) {
        //     square_bytes[i] = in[i];
        // }

        // print the square bytes
        std::cout << "Square Bytes: " << std::endl;
        for (int i = 0; i < n_bytes; ++i) {
            // Use std::setw and std::setfill to print two-digit hex numbers
            std::cout << std::setfill('0') << std::setw(2)
                    << std::hex << static_cast<int>(static_cast<unsigned char>(square_bytes[i])) << " ";
            if (i % 12 == 11) {
                std::cout << std::endl;
            }
        }
        // first interleaving (bit priority)
        for (int k = 0; k < n_sym; ++k) { // number of symbols
            // place the first packet in symbol_bytes
            for (int i = 0; i < 12; ++i) {
                symbol_bytes[i] = square_bytes[i + k * 12];
            }
            // interleave the symbol
            reorderBits(symbol_bytes, step_in_bytes, priority_matrix);
            reorderBits(step_in_bytes, step_out_bytes, significance_matrix);
            // place the interleaved symbol to the output
            for (int i = 0; i < 12; ++i) {
                out[i + k * 12] = step_out_bytes[i];
            }
        }
    }else{ // reverse interleaving
        // Calculate the inverse matrix============================
        std::vector<int> inverse_priority_matrix(96);
        std::vector<int> inverse_significance_matrix(96);

        for (int i = 0; i < priority_matrix.size(); ++i) {// Calculate the inverse priority matrix
            inverse_priority_matrix[priority_matrix[i]] = i;
        }
        for (int i = 0; i < significance_matrix.size(); ++i) {// Calculate the inverse significance_matrix 
            inverse_significance_matrix[significance_matrix[i]] = i;
        }
        // undo interleaving significance then priority
        for (int k = 0; k < n_sym; ++k) { // number of symbols
            // place the first packet in symbol_bytes
            for (int i = 0; i < 12; ++i) {
                symbol_bytes[i] = in[i + k * 12];
            }
            // interleave the symbol
            reorderBits(symbol_bytes, step_in_bytes, inverse_significance_matrix);
            reorderBits(step_in_bytes, step_out_bytes, inverse_priority_matrix);
            // place the interleaved symbol to the output
            for (int i = 0; i < 12; ++i) {
                square_bytes[i + k * 12] = step_out_bytes[i];
            }
        }

        // undo the byte shift alignment
        // Bytes were moved from index 24 and 25 to the end of the array
        int bytes_to_move = 2;
        int original_position = 24;  // The original starting position of the last two bytes in the 26-byte segment

        // Extract the two bytes from the end of the array
        char last_two_bytes[2];
        std::memcpy(last_two_bytes, square_bytes + n_bytes - bytes_to_move, bytes_to_move);
        // Shift the rest of the array right by two positions from original_position to the end - bytes_to_move
        std::memmove(square_bytes + original_position + bytes_to_move, square_bytes + original_position, n_bytes - original_position - bytes_to_move);
        // Place the extracted bytes back at their original position
        std::memcpy(square_bytes + original_position, last_two_bytes, bytes_to_move);

        for (int i = 0; i < n_bytes; i++) {
            out[i] = square_bytes[i];
        }
    }
}
