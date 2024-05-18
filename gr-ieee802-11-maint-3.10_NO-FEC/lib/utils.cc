/*
 * Copyright (C) 2013 Bastian Bloessl <bloessl@ccs-labs.org>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include "utils.h"

#include <math.h>
#include <cassert>
#include <cstring>

#include <vector>
#include <iomanip>

using gr::ieee802_11::BPSK_1_2;
using gr::ieee802_11::BPSK_3_4;
using gr::ieee802_11::QPSK_1_2;
using gr::ieee802_11::QPSK_3_4;
using gr::ieee802_11::QAM16_1_2;
using gr::ieee802_11::QAM16_3_4;
using gr::ieee802_11::QAM64_2_3;
using gr::ieee802_11::QAM64_3_4;

ofdm_param::ofdm_param(Encoding e)
{
    encoding = e;

    switch (e) {
    case BPSK_1_2:
        n_bpsc = 1; // number of coded bits per sub carrier
        n_cbps = 48; // number of coded bits per OFDM symbol
        n_dbps = 48; // number of data bits per OFDM symbol //was 24
        rate_field = 0x0D; // 0b00001101
        break;

    case BPSK_3_4:
        n_bpsc = 1;
        n_cbps = 48;
        n_dbps = 48; //36
        rate_field = 0x0F; // 0b00001111
        break;

    case QPSK_1_2:
        n_bpsc = 2;
        n_cbps = 96;
        n_dbps = 96; //48
        rate_field = 0x05; // 0b00000101
        break;

    case QPSK_3_4:
        n_bpsc = 2;
        n_cbps = 96;
        n_dbps = 96; //72
        rate_field = 0x07; // 0b00000111
        break;

    case QAM16_1_2:
        n_bpsc = 4;
        n_cbps = 192;
        n_dbps = 192; //96
        rate_field = 0x09; // 0b00001001
        break;

    case QAM16_3_4:
        n_bpsc = 4;
        n_cbps = 192;
        n_dbps = 192; //144
        rate_field = 0x0B; // 0b00001011
        break;

    case QAM64_2_3:
        n_bpsc = 6;
        n_cbps = 288;
        n_dbps = 288; //192
        rate_field = 0x01; // 0b00000001
        break;

    case QAM64_3_4:
        n_bpsc = 6;
        n_cbps = 288;
        n_dbps = 288; //216
        rate_field = 0x03; // 0b00000011
        break;
    default:
        assert(false);
        break;
    }
}


void ofdm_param::print()
{
    std::cout << "OFDM Parameters:" << std::endl;
    std::cout << "endcoding :" << encoding << std::endl;
    std::cout << "rate_field :" << (int)rate_field << std::endl; // rate field of the SIGNAL header
    std::cout << "n_bpsc :" << n_bpsc << std::endl; // number of coded bits per sub carrier
    std::cout << "n_cbps :" << n_cbps << std::endl; // number of coded bits per OFDM symbol
    std::cout << "n_dbps :" << n_dbps << std::endl; // number of data bits per OFDM symbol
}


frame_param::frame_param(ofdm_param& ofdm, int psdu_length)
{

    psdu_size = psdu_length; // size of the PSDU in bytes

    // number of symbols (17-11)
    n_sym = (int)ceil((16 + 8 * psdu_size + 6) / (double)ofdm.n_dbps);

    n_data_bits = n_sym * ofdm.n_dbps;  // total number of data bits, including service and padding (17-12)

    // number of padding bits (17-13)
    n_pad = n_data_bits - (16 + 8 * psdu_size + 6);

    n_encoded_bits = n_sym * ofdm.n_cbps; // total number of encoded bits
}
void frame_param::print()
{
    std::cout << "FRAME Parameters:" << std::endl;
    std::cout << "psdu_size: " << psdu_size << std::endl;
    std::cout << "n_sym: " << n_sym << std::endl;
    std::cout << "n_pad: " << n_pad << std::endl;
    std::cout << "n_encoded_bits: " << n_encoded_bits << std::endl;
    std::cout << "n_data_bits: " << n_data_bits << std::endl;
}


void scramble(const char* in, char* out, frame_param& frame, char initial_state)
// lsfr with polynomial x^6 + x^3 + 1
{

    int state = initial_state;
    int feedback;

    for (int i = 0; i < frame.n_data_bits; i++) {

        feedback = (!!(state & 64)) ^ (!!(state & 8));
        out[i] = feedback ^ in[i];
        state = ((state << 1) & 0x7e) | feedback;
    }
}


void reset_tail_bits(char* scrambled_data, frame_param& frame)
// reset the last 6 tail bytes to zero
{
    memset(scrambled_data + frame.n_data_bits - frame.n_pad - 6, 0, 6 * sizeof(char));
}


int ones(int n)
// count number of ones in binary representation of n
{
    int sum = 0;
    for (int i = 0; i < 8; i++) {
        if (n & (1 << i)) {
            sum++;
        }
    }
    return sum;
}


void convolutional_encoding(const char* in, char* out, frame_param& frame)
// convolutional encoding with 0155 and 0117 (octal), 0b0110_1101 and 0b0111_1111
{

    int state = 0;

    for (int i = 0; i < frame.n_data_bits; i++) {
        assert(in[i] == 0 || in[i] == 1);
        state = ((state << 1) & 0x7e) | in[i];
        out[i * 2] = ones(state & 0155) % 2;
        out[i * 2 + 1] = ones(state & 0117) % 2;
    }
}


void puncturing(const char* in, char* out, frame_param& frame, ofdm_param& ofdm)
{

    int mod;

    for (int i = 0; i < frame.n_data_bits * 2; i++) {
        switch (ofdm.encoding) {
        case BPSK_1_2:
        case QPSK_1_2:
        case QAM16_1_2:
            *out = in[i];
            out++;
            break;

        case QAM64_2_3:
            if (i % 4 != 3) {
                *out = in[i];
                out++;
            }
            break;

        case BPSK_3_4:
        case QPSK_3_4:
        case QAM16_3_4:
        case QAM64_3_4:
            mod = i % 6;
            if (!(mod == 3 || mod == 4)) {
                *out = in[i];
                out++;
            }
            break;
        default:
            assert(false);
            break;
        }
    }
}


void interleave(
    const char* in, char* out, frame_param& frame, ofdm_param& ofdm, bool reverse)
{

    int n_cbps = ofdm.n_cbps; // number of coded bits per OFDM symbol
    // Define arrays to hold the indices after the first and second permutations
    int first[MAX_BITS_PER_SYM];
    int second[MAX_BITS_PER_SYM];
    int s = std::max(ofdm.n_bpsc / 2, 1); // number of sub carriers per sub block

    // First permutation: Calculates the index mapping for the first permutation
    for (int j = 0; j < n_cbps; j++) {
        first[j] = s * (j / s) + ((j + int(floor(16.0 * j / n_cbps))) % s); 
    }

    // Second permutation: Calculates the index mapping for the second permutation
    for (int i = 0; i < n_cbps; i++) {
        second[i] = 16 * i - (n_cbps - 1) * int(floor(16.0 * i / n_cbps)); // 16*i - floor(16*i/n_cbps)*(n_cbps-1)
    }

    // Perform the interleaving or de-interleaving for each symbol in the frame
    for (int i = 0; i < frame.n_sym; i++) {
        for (int k = 0; k < n_cbps; k++) {
            if (reverse) {
                out[i * n_cbps + second[first[k]]] = in[i * n_cbps + k];
            } else {
                out[i * n_cbps + k] = in[i * n_cbps + second[first[k]]];
            }
        }
    }
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
void interleave2(const char* in, char* out, frame_param& frame, ofdm_param& ofdm, bool reverse){
    int n_cbps = ofdm.n_cbps; // number of coded bits per OFDM symbol
    int n_sym = frame.n_sym;
    std::cout << "n_cbps: " << n_cbps << std::endl;
    std::cout << "n_sym: " << n_sym << std::endl;
    // print number of bytes in the input
    std::cout << "n_bytes: " << n_sym*4*3 << std::endl;

    if (n_cbps != 96) {
        // use the normal interleave function
        std::cout << "Using normal interleave function!?" << std::endl;
        return interleave(in, out, frame, ofdm, reverse);
    }
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

    int n_bytes = n_sym*4*3; // 4 bytes per 32 bit float, 3 floats per symbol
    char square_bytes[n_bytes] = {};

    // print the square bytes
    std::cout << "in Bytes: " << std::endl;
    for (int i = 0; i < n_bytes; ++i) {
        // Use std::setw and std::setfill to print two-digit hex numbers
        std::cout << std::setfill('0') << std::setw(2)
                << std::hex << static_cast<int>(static_cast<char>(in[i])) << " ";
        if (i % 12 == 11) {
            std::cout << std::endl;
        }
    }

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


void split_symbols(const char* in, char* out, frame_param& frame, ofdm_param& ofdm)
// split the interleaved data into OFDM symbols
{

    int symbols = frame.n_sym * 48;

    for (int i = 0; i < symbols; i++) {
        out[i] = 0;
        for (int k = 0; k < ofdm.n_bpsc; k++) {
            assert(*in == 1 || *in == 0);
            out[i] |= (*in << k);
            in++;
        }
    }
}


void generate_bits(const char* psdu, char* data_bits, frame_param& frame)
// generate the WIFI data field, adding service field and pad bits
{
    // first 16 bits are zero (SERVICE/DATA field)
    memset(data_bits, 0, 16); // set first 16 bits to zero
    data_bits += 16; // offset the pointer by length of SERVICE/DATA field

    for (int i = 0; i < frame.psdu_size; i++) { // copy the PSDU, i is byte index
        for (int b = 0; b < 8; b++) { // bit order is LSB-MSB
            data_bits[i * 8 + b] = !!(psdu[i] & (1 << b)); // copy bit, ensure 0 or 1
        }
    }
    // print the data bits
    // std::cout << "Data Bits: " << std::endl;
    // for (int i = 0; i < frame.n_data_bits; ++i) {
    //     std::cout << (int)data_bits[i];
    //     if ((i + 1) % 8 == 0) {
    //         std::cout << " ";
    //     }
    // }
}

// void print_bytes(const char* out_bytes, int size)
// {
//     std::cout << std::endl;
//     for (int i = 0; i < size + 2; i++) {
//         if ((out_bytes[i] > 31) && (out_bytes[i] < 127)) {
//             std::cout << ((char)out_bytes[i]);
//         } else {
//             std::cout << ".";
//         }
//         //wrap around every 16 bytes
//         if ((i + 1) % 16 == 0) {
//             std::cout << std::endl;
//         }
//     }
//     std::cout << std::endl;
// }
