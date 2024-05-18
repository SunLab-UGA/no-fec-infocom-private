/*
 * Copyright (C) 2013, 2016 Bastian Bloessl <bloessl@ccs-labs.org>
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
#include <ieee802_11/decode_mac.h>

#include "utils.h"
#include "viterbi_decoder/viterbi_decoder.h"

#include <gnuradio/io_signature.h>
#include <boost/crc.hpp>
#include <iomanip>

using namespace gr::ieee802_11;

#define LINKTYPE_IEEE802_11 105 /* http://www.tcpdump.org/linktypes.html */

class decode_mac_impl : public decode_mac
{

public:
    decode_mac_impl(bool log, bool debug)
        : block("decode_mac",
                gr::io_signature::make(1, 1, 48),
                gr::io_signature::make(0, 0, 0)),
          d_log(log),
          d_debug(debug),
          d_ofdm(BPSK_1_2),
          d_frame(d_ofdm, 0),
          d_frame_complete(true)
    {
        message_port_register_out(pmt::mp("out"));
    }

    int general_work(int noutput_items,
                     gr_vector_int& ninput_items,
                     gr_vector_const_void_star& input_items,
                     gr_vector_void_star& output_items)
    {

        const uint8_t* in = (const uint8_t*)input_items[0];

        int i = 0;

        std::vector<gr::tag_t> tags;
        const uint64_t nread = this->nitems_read(0);

        // dout << "Decode MAC: input " << ninput_items[0] << std::endl;

        while (i < ninput_items[0]) {

            get_tags_in_range(tags, 0, nread + i, nread + i + 1);

            if (tags.size()) {
                if (d_frame_complete == false) {
                    // dout << "Warning: starting to receive new frame before old frame was "
                    //         "complete"
                    //      << std::endl;
                    // dout << "Already copied " << copied << " out of " << d_frame.n_sym
                    //      << " symbols of last frame" << std::endl;
                }
                d_frame_complete = false;

                // Enter tags into metadata dictionary
                d_meta = pmt::make_dict();
                for (auto tag : tags)
                    d_meta = pmt::dict_add(d_meta, tag.key, tag.value);

                int len_data = pmt::to_uint64(pmt::dict_ref(
                    d_meta, pmt::mp("frame bytes"), pmt::from_uint64(MAX_PSDU_SIZE + 1)));
                int encoding = pmt::to_uint64(
                    pmt::dict_ref(d_meta, pmt::mp("encoding"), pmt::from_uint64(0)));

                ofdm_param ofdm = ofdm_param((Encoding)encoding);
                frame_param frame = frame_param(ofdm, len_data);

                //DEBUG_MSG
                // std::cout << "Decode MAC: frame start -- len " << len_data << "  symbols "
                //           << frame.n_sym << "  encoding " << encoding
                //           << "  n_cbps "<< ofdm.n_cbps << std::endl;

                // check for maximum frame size
                if (frame.n_sym <= MAX_SYM && frame.psdu_size <= MAX_PSDU_SIZE) {
                    d_ofdm = ofdm;
                    d_frame = frame;
                    copied = 0;
                    // std::cout << "VALID Decode MAC: frame start -- len " << len_data << "  symbols "
                    //      << frame.n_sym << "  encoding " << encoding << std::endl;
                } else {
                    // std::cout << "Dropping frame which is too large (symbols or bits)"
                    //      << std::endl;
                }
            }

            if (copied < d_frame.n_sym) {
                // removed verbose debug output
                // if(copied % 24 == 0)
                //     std::cout << "symbols, copied " << copied << " out of "
                //         << d_frame.n_sym << std::endl;
                std::memcpy(d_rx_symbols + (copied * 48), in, 48);
                copied++;

                if (copied == d_frame.n_sym) {
                    // std::cout << "received complete frame - decoding " << copied << std::endl;
                    // add the raw symbols to the PMT
                    d_meta = pmt::dict_add(d_meta,
                                           pmt::mp("symbols"),
                                           pmt::make_blob(d_rx_symbols, 48 * d_frame.n_sym));
                    decode();
                    in += 48; // increment by one symbol
                    i++;
                    d_frame_complete = true;
                    break;
                }
            }

            in += 48;
            i++;
        }

        consume(0, i);

        return 0;
    }

    void decode()
    {

        for (int i = 0; i < d_frame.n_sym * 48; i++) {
            for (int k = 0; k < d_ofdm.n_bpsc; k++) {
                d_rx_bits[i * d_ofdm.n_bpsc + k] = !!(d_rx_symbols[i] & (1 << k));
            }
        }

        deinterleave();
        // deinterleave2();
        
        //EDITED TO REMOVE MOST FEC FUNCTIONALITY (BESIDES INTERLEAVING)
        //uint8_t* decoded = d_decoder.decode(&d_ofdm, &d_frame, d_deinterleaved_bits);
        uint8_t* decoded = d_deinterleaved_bits;

        descramble(decoded);
        // print_output();

        
        boost::crc_32_type result;
        result.process_bytes(out_bytes + 2, d_frame.psdu_size);// skip service field
        if (result.checksum() != 558161692) {
            // dout << "checksum wrong -- dropping" << std::endl;
            // return;
            // new behavior is to keep the frame even if the checksum is wrong, notify
            // dout << "INFO: checksum wrong" << std::endl;
        }

        mylog("encoding: {} - length: {} - symbols: {}",
              d_ofdm.encoding,
              d_frame.psdu_size,
              d_frame.n_sym);

        // create PDU
        // pmt::pmt_t blob = pmt::make_blob(out_bytes + 2, d_frame.psdu_size - 4); // remove FCS (4 bytes)
        pmt::pmt_t blob = pmt::make_blob(out_bytes + 2, d_frame.psdu_size); // keep FCS (4 bytes)
        // add metadata
        d_meta =
            pmt::dict_add(d_meta, pmt::mp("dlt"), pmt::from_long(LINKTYPE_IEEE802_11));
                

        message_port_pub(pmt::mp("out"), pmt::cons(d_meta, blob));
    }

    void deinterleave()
    {
        
        int n_cbps = d_ofdm.n_cbps;
        int first[MAX_BITS_PER_SYM];
        int second[MAX_BITS_PER_SYM];
        int s = std::max(d_ofdm.n_bpsc / 2, 1);

        for (int j = 0; j < n_cbps; j++) {
            first[j] = s * (j / s) + ((j + int(floor(16.0 * j / n_cbps))) % s);
        }

        for (int i = 0; i < n_cbps; i++) {
            second[i] = 16 * i - (n_cbps - 1) * int(floor(16.0 * i / n_cbps));
        }

        int count = 0;
        for (int i = 0; i < d_frame.n_sym; i++) {
            for (int k = 0; k < n_cbps; k++) {
                d_deinterleaved_bits[i * n_cbps + second[first[k]]] =
                    d_rx_bits[i * n_cbps + k];
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
    // Helper Function to reorder bits based on a index matrix
    void reorderBits(const char* input, char* output, const std::vector<int>& index_matrix) {
        for (int i = 0; i < 96; ++i) {  // 96 bits in 12 bytes
            bool bitValue = getBit(input, i);
            setBit(output, index_matrix[i], bitValue);
        }
    }
    // Helper Function to reverse bits in a byte
    unsigned char reverse_bits(unsigned char byte) {
        byte = (byte & 0xF0) >> 4 | (byte & 0x0F) << 4;
        byte = (byte & 0xCC) >> 2 | (byte & 0x33) << 2;
        byte = (byte & 0xAA) >> 1 | (byte & 0x55) << 1;
        return byte;
    }

    // Interleave knowing the data is 32 bit floats (keep msb close to the pilot "poles")
    // MODIFIED FROM UTILS.H !!! (it is not the same)
    void deinterleave2(){
        int n_cbps = d_ofdm.n_cbps; // number of coded bits per OFDM symbol
        int n_sym = d_frame.n_sym;
        std::cout << "n_cbps: " << n_cbps << std::endl;
        std::cout << "frames: " << n_sym << std::endl;

        if (n_cbps != 96) {
            // use the normal interleave function
            std::cout << "Using normal interleave function!?" << std::endl;
            return deinterleave();
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

        bool reverse = true; // always deinterleave

        if (!reverse){ // forward interleaving
            // byte shift to align with 32 bit boundaries (packet wide)
            int bytes_to_move = 2;
            int move_from_index  = 24;  // Start of the last two bytes in the 26-byte segment

            // Move the entire content up to the bytes to be moved
            std::memmove(square_bytes, d_rx_bits, move_from_index);
            // Shift the rest of the array left by two positions to fill the gap
            std::memmove(square_bytes + move_from_index, d_rx_bits + move_from_index + bytes_to_move, n_bytes - move_from_index - bytes_to_move);
            // Place the two moved bytes at the end of the total_size array
            std::memcpy(square_bytes + n_bytes - bytes_to_move, d_rx_bits + move_from_index, bytes_to_move);
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
                    d_deinterleaved_bits[i + k * 12] = step_out_bytes[i];
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
                    symbol_bytes[i] = d_rx_bits[i + k * 12];
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
                d_deinterleaved_bits[i] = square_bytes[i];
            }
        }
    }

    void descramble(uint8_t* decoded_bits)
    {

        int state = 0;
        std::memset(out_bytes, 0, d_frame.psdu_size + 2);

        for (int i = 0; i < 7; i++) {
            if (decoded_bits[i]) {
                state |= 1 << (6 - i);
            }
        }
        out_bytes[0] = state;

        int feedback;
        int bit;

        for (int i = 7; i < d_frame.psdu_size * 8 + 16; i++) {
            feedback = ((!!(state & 64))) ^ (!!(state & 8));
            bit = feedback ^ (decoded_bits[i] & 0x1);
            out_bytes[i / 8] |= bit << (i % 8);
            state = ((state << 1) & 0x7e) | feedback;
        }
    }

    void print_output()
    {

        std::cout << std::endl;
        std::cout << "psdu size" << d_frame.psdu_size << std::endl;
        for (int i = 0; i < d_frame.psdu_size + 2; i++) {
            // dout << std::setfill('0') << std::setw(2) << std::hex
            //      << ((unsigned int)out_bytes[i] & 0xFF) << std::dec << " ";
            if (i % 16 == 15) {
                // dout << std::endl;
            }
        }
        std::cout << std::endl;
        for (int i = 0; i < d_frame.psdu_size + 2; i++) {
            if ((out_bytes[i] > 31) && (out_bytes[i] < 127)) {
                std::cout << ((char)out_bytes[i]);
            } else {
                std::cout << ".";
            }
        }
        std::cout << std::endl;
    }

private:
    bool d_debug;
    bool d_log;

    pmt::pmt_t d_meta;

    frame_param d_frame;
    ofdm_param d_ofdm;

    viterbi_decoder d_decoder;

    uint8_t d_rx_symbols[48 * MAX_SYM];
    uint8_t d_rx_bits[MAX_ENCODED_BITS];
    uint8_t d_deinterleaved_bits[MAX_ENCODED_BITS];
    uint8_t out_bytes[MAX_PSDU_SIZE + 2]; // 2 for signal field

    int copied;
    bool d_frame_complete;
};

decode_mac::sptr decode_mac::make(bool log, bool debug)
{
    return gnuradio::get_initial_sptr(new decode_mac_impl(log, debug));
}
