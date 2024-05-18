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
#include <ieee802_11/parse_mac.h>

#include <gnuradio/block_detail.h>
#include <gnuradio/io_signature.h>
#include <string>
#include <iomanip>

//TOGGLE FOR DEBUGGING
// #define DEBUG 1
#ifdef DEBUG
#define DEBUG_MSG(msg) dout << msg << std::endl;
#else
#define DEBUG_MSG(msg)
#endif

using namespace gr::ieee802_11;

class parse_mac_impl : public parse_mac
{

public:
    parse_mac_impl(bool log, bool debug)
        : block("parse_mac",
                gr::io_signature::make(0, 0, 0),
                gr::io_signature::make(0, 0, 0)),
          d_log(log),
          d_last_seq_no(-1),
          d_debug(debug)
    {

        message_port_register_in(pmt::mp("in"));
        set_msg_handler(
            pmt::mp("in"),
            boost::bind(&parse_mac_impl::parse, this, boost::placeholders::_1));

        message_port_register_out(pmt::mp("out"));
    }

    ~parse_mac_impl() {}

    void parse(pmt::pmt_t pdu)
    {

        if (pmt::is_eof_object(pdu)) {
            detail().get()->set_done(true);
            return;
        } else if (pmt::is_symbol(pdu)) {
            return;
        }

        d_meta = pmt::car(pdu);
        d_msg = pmt::cdr(pdu);

        int frame_len = pmt::blob_length(d_msg);
        mac_header* h = (mac_header*)pmt::blob_data(d_msg);

        mylog("length: {}",frame_len);

        // dout << std::endl << "new mac frame  (length " << frame_len << ")" << std::endl;
        DEBUG_MSG(std::endl << "new mac frame  (length " << frame_len << ")")
        // dout << "=========================================" << std::endl;
        DEBUG_MSG("=========================================");
        if (frame_len < 20) {
            // dout << "frame too short to parse (<20)" << std::endl;
            DEBUG_MSG("frame too short to parse (<20)");
            return;
        }

        d_meta = pmt::dict_add(d_meta, pmt::mp("duration"), pmt::mp(h->duration));

#define HEX(a) std::hex << std::setfill('0') << std::setw(2) << int(a) << std::dec
        // dout << "duration: " << HEX(h->duration >> 8) << " " << HEX(h->duration & 0xff)
        //      << std::endl;
        // dout << "frame control: " << HEX(h->frame_control >> 8) << " "
        //      << HEX(h->frame_control & 0xff);

        DEBUG_MSG("duration: " << HEX(h->duration >> 8) << " " << HEX(h->duration & 0xff))
        DEBUG_MSG("frame control: " << HEX(h->frame_control >> 8) << " "
                                   << HEX(h->frame_control & 0xff))

        switch ((h->frame_control >> 2) & 3) {

        case 0:
            d_meta = pmt::dict_add(d_meta, pmt::mp("type"), pmt::mp("management"));
            // dout << " (MANAGEMENT)" << std::endl;
            DEBUG_MSG(" (MANAGEMENT)")
            parse_management((char*)h, frame_len);
            break;
        case 1:
            d_meta = pmt::dict_add(d_meta, pmt::mp("type"), pmt::mp("Control"));
            // dout << " (CONTROL)" << std::endl;
            DEBUG_MSG(" (CONTROL)")
            parse_control((char*)h, frame_len);
            break;

        case 2:
            d_meta = pmt::dict_add(d_meta, pmt::mp("type"), pmt::mp("Data"));
            // dout << " (DATA)" << std::endl;
            DEBUG_MSG(" (DATA)")
            parse_data((char*)h, frame_len);
            break;

        default:
            d_meta = pmt::dict_add(d_meta, pmt::mp("type"), pmt::mp("Unknown"));
            // dout << " (unknown)" << std::endl;
            DEBUG_MSG(" (unknown)")
            break;
        }

        char* frame = (char*)pmt::blob_data(d_msg);

        // DATA
        if ((((h->frame_control) >> 2) & 63) == 2) {
            print_ascii(frame + 24, frame_len - 24);
            // QoS Data
        } else if ((((h->frame_control) >> 2) & 63) == 34) {
            print_ascii(frame + 26, frame_len - 26);
        }

        message_port_pub(pmt::mp("out"), pmt::cons(d_meta, d_msg));
    }

    void parse_management(char* buf, int length)
    {
        mac_header* h = (mac_header*)buf;

        if (length < 24) {
            //dout << "too short for a management frame" << std::endl;
            DEBUG_MSG("too short for a management frame");
            return;
        }

        //dout << "Subtype: ";
        DEBUG_MSG("Subtype: ");
        switch (((h->frame_control) >> 4) & 0xf) {
        case 0:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Association Request"));
            //dout << "Association Request";
            DEBUG_MSG("Association Request");
            break;
        case 1:
            d_meta = pmt::dict_add(
                d_meta, pmt::mp("subtype"), pmt::mp("Association Response"));
            //dout << "Association Response";
            DEBUG_MSG("Association Response");
            break;
        case 2:
            d_meta = pmt::dict_add(
                d_meta, pmt::mp("subtype"), pmt::mp("Reassociation Request"));
            //dout << "Reassociation Request";
            DEBUG_MSG("Reassociation Request");
            break;
        case 3:
            d_meta = pmt::dict_add(
                d_meta, pmt::mp("subtype"), pmt::mp("Reassociation Response"));
            //dout << "Reassociation Response";
            DEBUG_MSG("Reassociation Response");
            break;
        case 4:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Probe Request"));
            //dout << "Probe Request";
            DEBUG_MSG("Probe Request");
            break;
        case 5:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Probe Response"));
            //dout << "Probe Response";
            DEBUG_MSG("Probe Response");
            break;
        case 6:
            d_meta = pmt::dict_add(
                d_meta, pmt::mp("subtype"), pmt::mp("Timing Advertisement"));
            //dout << "Timing Advertisement";
            DEBUG_MSG("Timing Advertisement");
            break;
        case 7:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Reserved"));
            //dout << "Reserved";
            DEBUG_MSG("Reserved");
            break;
        case 8:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Beacon"));
            //dout << "Beacon" << std::endl;
            DEBUG_MSG("Beacon");
            if (length < 38) {
                return;
            }
            {
                uint8_t* len = (uint8_t*)(buf + 24 + 13);
                if (length < 38 + *len) {
                    return;
                }
                std::string s(buf + 24 + 14, *len);
                d_meta = pmt::dict_add(d_meta, pmt::mp("ssid"), pmt::mp(s));
                //dout << "SSID: " << s;
                DEBUG_MSG("SSID: " << s);
            }
            break;
        case 9:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("ATIM"));
            //dout << "ATIM";
            DEBUG_MSG("ATIM");
            break;
        case 10:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Disassociation"));
            //dout << "Disassociation";
            DEBUG_MSG("Disassociation");
            break;
        case 11:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Authentication"));
            //dout << "Authentication";
            DEBUG_MSG("Authentication");
            break;
        case 12:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Deauthentication"));
            //dout << "Deauthentication";
            DEBUG_MSG("Deauthentication");
            break;
        case 13:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Action"));
            //dout << "Action";
            DEBUG_MSG("Action");
            break;
        case 14:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Action No Ack"));
            //dout << "Action No Ack";
            DEBUG_MSG("Action No Ack");
            break;
        case 15:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Reserved"));
            //dout << "Reserved";
            DEBUG_MSG("Reserved");
            break;
        default:
            break;
        }
        //dout << std::endl;

    int seq_no = int(h->seq_nr >> 4);
    d_meta = pmt::dict_add(d_meta, pmt::mp("sequence number"), pmt::mp(seq_no));
    //dout << "seq nr: " << seq_no << std::endl;
    DEBUG_MSG("seq nr: " << std::to_string(seq_no));

    auto address = format_mac_address(h->addr1);
    d_meta = pmt::dict_add(d_meta, pmt::mp("address 1"), pmt::mp(address));
    //dout << "address 1: " << address << std::endl;
    DEBUG_MSG("address 1: " << address);

    address = format_mac_address(h->addr2);
    d_meta = pmt::dict_add(d_meta, pmt::mp("address 2"), pmt::mp(address));
    //dout << "address 2: " << address << std::endl;
    DEBUG_MSG("address 2: " << address);

    address = format_mac_address(h->addr3);
    d_meta = pmt::dict_add(d_meta, pmt::mp("address 3"), pmt::mp(address));
    //dout << "address 3: " << address << std::endl;
    DEBUG_MSG("address 3: " << address);
    }

    void parse_data(char* buf, int length)
    {
        mac_header* h = (mac_header*)buf;
        if (length < 24) {
            // dout << "too short for a data frame" << std::endl;
            DEBUG_MSG("too short for a data frame")
            return;
        }

        // dout << "Subtype: ";
        DEBUG_MSG("Subtype: ");
        switch (((h->frame_control) >> 4) & 0xf) {
        case 0:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Data"));
            // dout << "Data";
            DEBUG_MSG("Data");
            break;
        case 1:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Data + CF-ACK"));
            // dout << "Data + CF-ACK";
            DEBUG_MSG("Data + CF-ACK");
            break;
        case 2:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Data + CR-Poll"));
            // dout << "Data + CR-Poll";
            DEBUG_MSG("Data + CR-Poll");
            break;
        case 3:
            d_meta = pmt::dict_add(
                d_meta, pmt::mp("subtype"), pmt::mp("Data + CF-ACK + CF-Poll"));
            // dout << "Data + CF-ACK + CF-Poll";
            DEBUG_MSG("Data + CF-ACK + CF-Poll");
            break;
        case 4:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Null"));
            // dout << "Null";
            DEBUG_MSG("Null");
            break;
        case 5:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("CF-ACK"));
            // dout << "CF-ACK";
            DEBUG_MSG("CF-ACK");
            break;
        case 6:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("CF-Poll"));
            // dout << "CF-Poll";
            DEBUG_MSG("CF-Poll");
            break;
        case 7:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("CF-ACK + CF-Poll"));
            // dout << "CF-ACK + CF-Poll";
            DEBUG_MSG("CF-ACK + CF-Poll");
            break;
        case 8:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("QoS Data"));
            // dout << "QoS Data";
            DEBUG_MSG("QoS Data");
            break;
        case 9:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("QoS Data + CF-ACK"));
            // dout << "QoS Data + CF-ACK";
            DEBUG_MSG("QoS Data + CF-ACK");
            break;
        case 10:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("QoS Data + CF-Poll"));
            // dout << "QoS Data + CF-Poll";
            DEBUG_MSG("QoS Data + CF-Poll");
            break;
        case 11:
            d_meta = pmt::dict_add(
                d_meta, pmt::mp("subtype"), pmt::mp("QoS Data + CF-ACK + CF-Poll"));
            // dout << "QoS Data + CF-ACK + CF-Poll";
            DEBUG_MSG("QoS Data + CF-ACK + CF-Poll");
            break;
        case 12:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("QoS Null"));
            // dout << "QoS Null";
            DEBUG_MSG("QoS Null");
            break;
        case 13:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Reserved"));
            // dout << "Reserved";
            DEBUG_MSG("Reserved");
            break;
        case 14:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("QoS CF-Poll"));
            // dout << "QoS CF-Poll";
            DEBUG_MSG("QoS CF-Poll");
            break;
        case 15:
            d_meta = pmt::dict_add(
                d_meta, pmt::mp("subtype"), pmt::mp("QoS CF-ACK + CF-Poll"));
            // dout << "QoS CF-ACK + CF-Poll";
            DEBUG_MSG("QoS CF-ACK + CF-Poll");
            break;
        default:
            break;
        }
        // dout << std::endl;


        int seq_no = int(h->seq_nr >> 4);
        d_meta = pmt::dict_add(d_meta, pmt::mp("sequence number"), pmt::mp(seq_no));
        // dout << "seq nr: " << seq_no << std::endl;
        DEBUG_MSG("seq nr: " << seq_no);

        auto address = format_mac_address(h->addr1);
        d_meta = pmt::dict_add(d_meta, pmt::mp("address 1"), pmt::mp(address));
        // dout << "address 1: " << address << std::endl;
        DEBUG_MSG("address 1: " << address);

        address = format_mac_address(h->addr2);
        d_meta = pmt::dict_add(d_meta, pmt::mp("address 2"), pmt::mp(address));
        // dout << "address 2: " << address << std::endl;
        DEBUG_MSG("address 2: " << address);

        address = format_mac_address(h->addr3);
        d_meta = pmt::dict_add(d_meta, pmt::mp("address 3"), pmt::mp(address));
        // dout << "address 3: " << address << std::endl;
        DEBUG_MSG("address 3: " << address);


        float lost_frames = seq_no - d_last_seq_no - 1;
        if (lost_frames < 0)
            lost_frames += 1 << 12;
        d_meta = pmt::dict_add(d_meta, pmt::mp("lost frames"), pmt::mp(lost_frames));

        // calculate frame error rate
        float fer = lost_frames / (lost_frames + 1);
        // dout << "instantaneous fer: " << fer << std::endl;
        DEBUG_MSG("instantaneous fer: " << fer);
        d_meta = pmt::dict_add(d_meta, pmt::mp("instantaneous fer"), pmt::mp(fer));

        // keep track of sequence numbers
        d_last_seq_no = seq_no;
    }

    void parse_control(char* buf, int length)
    {
        mac_header* h = (mac_header*)buf;

        // dout << "Subtype: ";
        DEBUG_MSG("Subtype: ");
        switch (((h->frame_control) >> 4) & 0xf) {
        case 7:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Control Wrapper"));
            // dout << "Control Wrapper";
            DEBUG_MSG("Control Wrapper");
            break;
        case 8:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Block ACK Request"));
            // dout << "Block ACK Request";
            DEBUG_MSG("Block ACK Request");
            break;
        case 9:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Block ACK"));
            // dout << "Block ACK";
            DEBUG_MSG("Block ACK");
            break;
        case 10:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("PS Poll"));
            // dout << "PS Poll";
            DEBUG_MSG("PS Poll");
            break;
        case 11:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("RTS"));
            // dout << "RTS";
            DEBUG_MSG("RTS");
            break;
        case 12:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("CTS"));
            // dout << "CTS";
            DEBUG_MSG("CTS");
            break;
        case 13:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("ACK"));
            // dout << "ACK";
            DEBUG_MSG("ACK");
            break;
        case 14:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("CF-End"));
            // dout << "CF-End";
            DEBUG_MSG("CF-End");
            break;
        case 15:
            d_meta =
                pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("CF-End + CF-ACK"));
            // dout << "CF-End + CF-ACK";
            DEBUG_MSG("CF-End + CF-ACK");
            break;
        default:
            d_meta = pmt::dict_add(d_meta, pmt::mp("subtype"), pmt::mp("Reserved"));
            // dout << "Reserved";
            DEBUG_MSG("Reserved");
            break;
        }
        // dout << std::endl;


        auto address = format_mac_address(h->addr1);
        d_meta = pmt::dict_add(d_meta, pmt::mp("ra"), pmt::mp(address));
        // dout << "RA: " << address << std::endl;
        DEBUG_MSG("RA: " << address);

        address = format_mac_address(h->addr2);
        d_meta = pmt::dict_add(d_meta, pmt::mp("ta"), pmt::mp(address));
        // dout << "TA: " << address << std::endl;
        DEBUG_MSG("TA: " << address);
    }

    std::string format_mac_address(uint8_t* addr)
    {
        std::stringstream str;

        str << std::setfill('0') << std::hex << std::setw(2) << (int)addr[0];

        for (int i = 1; i < 6; i++) {
            str << ":" << std::setw(2) << (int)addr[i];
        }

        return str.str();
    }

    void print_ascii(char* buf, int length)
    {
        // dout << "RX: ";  // add a prefix to the first line
        DEBUG_MSG("RX: ")
        for (int i = 0; i < length; i++) {
            if ((buf[i] > 31) && (buf[i] < 127)) {
                // dout << buf[i];
                DEBUG_MSG(buf[i])
            } else {
                // dout << "."; // replace non-printable characters with a dot
                DEBUG_MSG(".")
            }
            // add a space after every 4 characters or 32 bits
            if ((i + 1) % 4 == 0) {
                // dout << " ";
                DEBUG_MSG(" ")
            }
        }
        // dout << std::endl;
        DEBUG_MSG(std::endl)
    }

private:
    bool d_log;
    bool d_debug;
    int d_last_seq_no;
    pmt::pmt_t d_meta;
    pmt::pmt_t d_msg;
};

parse_mac::sptr parse_mac::make(bool log, bool debug)
{
    return gnuradio::get_initial_sptr(new parse_mac_impl(log, debug));
}
