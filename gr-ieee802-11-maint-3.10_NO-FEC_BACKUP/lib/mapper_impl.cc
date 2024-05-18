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
#include "utils.h"
#include <gnuradio/io_signature.h>
#include <ieee802_11/mapper.h>
#include <iomanip>

using namespace gr::ieee802_11;

// memory max size checks
#define MAX_DATA_BITS (1 << 20) // 1,048,576 bits
#define MAX_ENCODED_BITS_MEM (2 * MAX_DATA_BITS) // 2,097,152 bits

class mapper_impl : public mapper
{
public:
    static const int DATA_CARRIERS = 48;

    mapper_impl(Encoding e, bool debug)
        : block("mapper",
                gr::io_signature::make(0, 0, 0),
                gr::io_signature::make(1, 1, sizeof(char))),
          d_symbols_offset(0),
          d_symbols(NULL),
          d_debug(debug),
          d_scrambler(1),
          d_ofdm(e)
    {

        message_port_register_in(pmt::mp("in"));
        set_encoding(e);
    }

    ~mapper_impl() { free(d_symbols); }

    void print_message(const char* msg, size_t len)
    {


        // dout << std::hex << "MAPPER input symbols" << std::endl
        //      << "===========================" << std::endl;

        for (int i = 0; i < len; i++) {
            // dout << std::hex << (int)msg[i] << " ";
        }

        // dout << std::dec << std::endl;
    }

    //print message to stdout (this will lag and not remain fast enough for real time)
    void print_message_stdout(const char* msg, size_t len)
    {
        std::cout << std::hex << "MAPPER input symbols" << std::endl
                  << "===========================" << std::endl;

        for (int i = 0; i < len; i++) {
            std::cout << std::hex << (int)msg[i] << " ";
        }

        std::cout << std::dec << std::endl;
    }


    int general_work(int noutput,
                     gr_vector_int& ninput_items,
                     gr_vector_const_void_star& input_items,
                     gr_vector_void_star& output_items)
    {

        unsigned char* out = (unsigned char*)output_items[0];
        // dout << "MAPPER called offset: " << d_symbols_offset
        //      << "   length: " << d_symbols_len << std::endl;
        while (!d_symbols_offset) {
            pmt::pmt_t msg(delete_head_nowait(pmt::intern("in")));

            if (!msg.get()) {
                return 0;
            }

            if (pmt::is_pair(msg)) {
                // dout << "MAPPER: received new message" << std::endl;
                gr::thread::scoped_lock lock(d_mutex);

                int psdu_length = pmt::blob_length(pmt::cdr(msg));
                const char* psdu =
                    static_cast<const char*>(pmt::blob_data(pmt::cdr(msg)));

                // ############ INSERT MAC STUFF
                frame_param frame(d_ofdm, psdu_length);
                if (frame.n_sym > MAX_SYM) {
                    std::cout << "packet too large, maximum number of symbols is "
                              << MAX_SYM << std::endl;
                    return 0;
                }
                
                if (frame.n_data_bits > MAX_DATA_BITS) { // check if data bits exceed maximum size
                    std::cout << "Error: Data bits exceed maximum allowed size." << std::endl;
                    return 0;
                }
                if (frame.n_encoded_bits > MAX_ENCODED_BITS_MEM) { // check if encoded bits exceed maximum size
                    std::cout << "Error: Encoded bits exceed maximum allowed size." << std::endl;
                    return 0;
                }


                // alloc memory for modulation steps
                char* data_bits = (char*)calloc(frame.n_data_bits, sizeof(char));
                if (!data_bits) { // check if memory was allocated
                    std::cout << "Failed to allocate memory for data_bits." << std::endl;
                    return 0;
                }
                char* scrambled_data = (char*)calloc(frame.n_data_bits, sizeof(char));
                if (!scrambled_data) { // check if memory was allocated
                    std::cout << "Failed to allocate memory for scrambled_data." << std::endl;
                    return 0;
                }
                // char* encoded_data = (char*)calloc(frame.n_data_bits * 2, sizeof(char));
                // char* punctured_data = (char*)calloc(frame.n_encoded_bits, sizeof(char));
                char* interleaved_data =
                    (char*)calloc(frame.n_encoded_bits, sizeof(char));
                if (!interleaved_data) { // check if memory was allocated
                    std::cout << "Failed to allocate memory for interleaved_data." << std::endl;
                    return 0;
                }
                char* symbols =
                    (char*)calloc((frame.n_encoded_bits / d_ofdm.n_bpsc), sizeof(char));
                if (!symbols) { // check if memory was allocated
                    std::cout << "Failed to allocate memory for symbols." << std::endl;
                    return 0;
                }
                // generate the WIFI data field, adding service field and pad bits
                generate_bits(psdu, data_bits, frame);

                // frame.print();

                //print out the length of the data bytes
                // std::cout << "(Generated) Data bits length: " << frame.n_data_bits << std::endl;

                
                // print_bits(data_bits, frame.psdu_size * 8);
                // print_bytes(data_bits, frame.psdu_size);

                // skip scrambling for now
                std::memcpy(scrambled_data, data_bits, frame.n_data_bits);

                // scrambling
                scramble(data_bits, scrambled_data, frame, d_scrambler++);
                if (d_scrambler > 127) {
                    d_scrambler = 1;
                }
                //EDITED TO REMOVE MOST FEC FUNCTIONALITY (BESIDES INTERLEAVING)

                // reset tail bits (6 bytes to zero)
                // reset_tail_bits(scrambled_data, frame);

                // encoding
                //convolutional_encoding(scrambled_data, encoded_data, frame);
                // puncturing
                //puncturing(encoded_data, punctured_data, frame, d_ofdm);
                // std::cout << "punctured" << std::endl;
                // interleaving
                //interleave(punctured_data, interleaved_data, frame, d_ofdm);
                interleave(scrambled_data, interleaved_data, frame, d_ofdm);
                // interleave2(scrambled_data, interleaved_data, frame, d_ofdm); //new interleaving function
                // std::cout << "Interleaved bits length: " << frame.n_encoded_bits << std::endl;
                // std::cout << "Interleaved bits: " << std::endl;
                // print_bits(interleaved_data, frame.n_encoded_bits);

                // split the data into symbols based on the modulation (ex. BPSK=1 bit per symbol)
                split_symbols(interleaved_data, symbols, frame, d_ofdm);

                d_symbols_len = frame.n_sym * 48;

                d_symbols = (char*)calloc(d_symbols_len, 1);
                std::memcpy(d_symbols, symbols, d_symbols_len);


                // add tags
                pmt::pmt_t key = pmt::string_to_symbol("packet_len");
                pmt::pmt_t value = pmt::from_long(d_symbols_len);
                pmt::pmt_t srcid = pmt::string_to_symbol(alias());
                add_item_tag(0, nitems_written(0), key, value, srcid);

                pmt::pmt_t psdu_bytes = pmt::from_long(psdu_length);
                add_item_tag(
                    0, nitems_written(0), pmt::mp("psdu_len"), psdu_bytes, srcid);

                pmt::pmt_t encoding = pmt::from_long(d_ofdm.encoding);
                add_item_tag(0, nitems_written(0), pmt::mp("encoding"), encoding, srcid);

                // print the frame parameters
                // std::cout << "#####-MAPPER-TX-#####" << std::endl;
                // frame.print();
                // d_ofdm.print();
                // // print_message_stdout(psdu, psdu_length);
                // // print_message_stdout(data_bits, frame.n_data_bits);
                // // print_message_stdout(scrambled_data, frame.n_data_bits);

                // // print_message_stdout(encoded_data, frame.n_data_bits * 2);
                // // print_message_stdout(punctured_data, frame.n_encoded_bits);

                // // print_message_stdout(interleaved_data, frame.n_encoded_bits);
                // // print_message_stdout(symbols, frame.n_encoded_bits / d_ofdm.n_bpsc);
                // std::cout << "####-TX-END-####" << std::endl;


                free(data_bits);
                free(scrambled_data);
                // free(encoded_data);
                // free(punctured_data);
                free(interleaved_data);
                free(symbols);

                break;
            }
        }

        int i = std::min(noutput, d_symbols_len - d_symbols_offset);
        std::memcpy(out, d_symbols + d_symbols_offset, i);
        d_symbols_offset += i;

        if (d_symbols_offset == d_symbols_len) {
            d_symbols_offset = 0;
            free(d_symbols);
            d_symbols = 0;
        }

        return i;
    }

    void set_encoding(Encoding encoding)
    {

        std::cout << "MAPPER: encoding: " << encoding << std::endl;
        gr::thread::scoped_lock lock(d_mutex);

        d_ofdm = ofdm_param(encoding);
    }

    void print_bits(const char* data_bits, int size) {
        for (int i = 0; i < size; i++) {
            std::cout << std::hex << static_cast<int>(data_bits[i]);
            // Print a space every 8 bits for readability
            if ((i + 1) % 8 == 0) {
                std::cout << " ";
            }
        }
        std::cout << std::endl;
    }
    // void print_bits(const char* data_bits, int size) {
    //     std::cout << "Hex Output: ";
    //     for (int i = 0; i < size; i++) {
    //         // Cast to unsigned char first to avoid sign extension, then to int
    //         std::cout << std::hex << std::setfill('0') << std::setw(2) 
    //                 << static_cast<int>(static_cast<unsigned char>(data_bits[i]));

    //         // Print a space every 8 bits (2 hex characters) for readability
    //         if ((i + 1) % 8 == 0) {
    //             std::cout << " ";
    //         }
    //     }
    //     std::cout << std::endl;
    // }

    void print_bytes(const char* out_bytes, int size){
        std::cout << std::endl;
        for (int i = 0; i < size + 2; i++) {
            if ((out_bytes[i] > 31) && (out_bytes[i] < 127)) {
                std::cout << static_cast<char>(out_bytes[i]);
            } else {
                std::cout << ".";
            }
            //wrap around every 16 bytes
            if ((i + 1) % 16 == 0) {
                std::cout << std::endl;
            }
        }
        std::cout << std::endl;
    }   

private:
    uint8_t d_scrambler;
    bool d_debug;
    char* d_symbols;
    int d_symbols_offset;
    int d_symbols_len;
    ofdm_param d_ofdm;
    gr::thread::mutex d_mutex;
};

mapper::sptr mapper::make(Encoding mcs, bool debug)
{
    return gnuradio::get_initial_sptr(new mapper_impl(mcs, debug));
}
