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
#ifndef INCLUDED_IEEE802_11_UTILS_H
#define INCLUDED_IEEE802_11_UTILS_H

#include <gnuradio/config.h>
#include <ieee802_11/api.h>
#include <ieee802_11/mapper.h>
#include <cinttypes>
#include <iostream>

using gr::ieee802_11::Encoding;

#define MAX_PAYLOAD_SIZE 1500
#define MAX_PSDU_SIZE (MAX_PAYLOAD_SIZE + 28) // MAC, CRC
#define MAX_SYM (((16 + 8 * MAX_PSDU_SIZE + 6) / 24) + 1)
#define MAX_BITS_PER_SYM 288
#define MAX_ENCODED_BITS ((16 + 8 * MAX_PSDU_SIZE + 6) * 2 + MAX_BITS_PER_SYM)

#define dout d_debug&& std::cout
#define mylog(...)                      \
    do {                                \
        if (d_log) {                    \
            d_logger->info(__VA_ARGS__); \
        }                               \
    } while (0);

#pragma pack(push, 1)
struct mac_header {
    // protocol version, type, subtype, to_ds, from_ds, ...
    uint16_t frame_control; // 16 bits
    uint16_t duration; // in microseconds
    uint8_t addr1[6]; // destination address, DA, (ToDS=0)
    uint8_t addr2[6]; // source address, RA, (FromDS=0)
    uint8_t addr3[6]; // BSSID (ToDS=0, FromDS=0)
    uint16_t seq_nr; // sequence number (4+12 bits, Fragment number + Sequence number)
};
#pragma pack(pop)

/**
 * WIFI parameters
 */
class ofdm_param
{
public:
    ofdm_param(Encoding e);

    // data rate
    Encoding encoding;
    char rate_field;  // rate field of the SIGNAL header
    int n_bpsc;  // number of coded bits per sub carrier
    int n_cbps;  // number of coded bits per OFDM symbol
    int n_dbps;  // number of data bits per OFDM symbol

    void print();
};

/**
 * packet specific parameters
 */
class frame_param
{
public:
    frame_param(ofdm_param& ofdm, int psdu_length);
    int psdu_size;  // PSDU size in bytes (Physical Layer Service Data Unit)
    int n_sym;  // number of OFDM symbols (17-11)
    int n_pad;  // number of padding bits in the DATA field (17-13)
    int n_encoded_bits;
    int n_data_bits;  // total number of data bits, including service and padding (17-12)

    void print();
};

/**
 * Given a payload, generates a MAC data frame (i.e., a PSDU) to be given
 * to the physical layer for encoding.
 *
 * \param msdu the payload for the MAC frame
 * \param msdu_size the size of the msdu in bytes
 * \param psdu pointer to a byte array where to store the MAC frame. Memory
 * will be alloced by the function
 * \param psdu_size pointer to an integer where the size of the psdu in bytes
 * will be stored
 * \param seq sequence number of the frame
 */
void generate_mac_data_frame(
    const char* msdu, int msdu_size, char** psdu, int* psdu_size, char seq);

void scramble(const char* input, char* out, frame_param& frame, char initial_state);

void reset_tail_bits(char* scrambled_data, frame_param& frame);

void convolutional_encoding(const char* input, char* out, frame_param& frame);

void puncturing(const char* input, char* out, frame_param& frame, ofdm_param& ofdm);

void interleave(const char* input,
                char* out,
                frame_param& frame,
                ofdm_param& ofdm,
                bool reverse = false);

void interleave2(const char* input,
                char* out,
                frame_param& frame,
                ofdm_param& ofdm,
                bool reverse = false);

void split_symbols(const char* input, char* out, frame_param& frame, ofdm_param& ofdm);

void generate_bits(const char* psdu, char* data_bits, frame_param& frame);

#endif /* INCLUDED_IEEE802_11_UTILS_H */
