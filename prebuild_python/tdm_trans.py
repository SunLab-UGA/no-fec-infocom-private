# from transceiver_float we derive a basic tdm link which tracks the sent and received packets

import zmq
import time
import pmt
import numpy as np
from typing import List
import logging


base_log_name = 'application.log'
time_suffix = time.strftime("%Y%m%d-%H%M%S")

logging.basicConfig(filename=f'application{time_suffix}.log',
                filemode= 'w',
                format='%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level=logging.INFO)
# print statement verbosity
VERBOSE = False

class transceiver:
    def __init__(self, address, tx_port, rx_port):
        self.address = address
        self.tx_port = tx_port
        self.rx_port = rx_port
        
        self.context = zmq.Context()
        self.tx_socket = self.context.socket(zmq.PUSH)
        self.tx_socket.bind(f"tcp://{address}:{tx_port}")

        self.rx_socket = self.context.socket(zmq.PULL)
        self.rx_socket.connect(f"tcp://{address}:{rx_port}")

        # self.received_data = [] # list of received data
        # self.sent_data = [] # list of sent data
        self.underrun = 0 # count of underruns
    # ======================================================================== INTERNAL FUNCTIONS
    def _check_if_empty(self, data) -> bool:
        '''Check if the data is empty'''
        if len(data) == 1 and data[0] == 0:
            return True
        else:
            return False

    def _decode_PMT(self, data:dict) -> tuple:
        '''Decode the data tuple from a PMT message
            data should be a tuple of (dict, np.array)'''
        try:
            data = pmt.deserialize_str(data) # deserialize the data
            data = pmt.to_python(data) # convert the data to a python object
        except Exception as e:
            print(f"ERROR: could not decode PMT message: {e}") if VERBOSE else None
            logging.error(f"ERROR: could not decode PMT message: {e}")
            return None,None

        # check if the data is 'empty', if so raise a warning and return 0
        if self._check_if_empty(data) == True:
            print("WARNING: empty data packet received!") if VERBOSE else None
            logging.warning("WARNING: empty data packet received!")
            return None,None # return empty lists

        # check if the the data is a tuple
        if type(data) != tuple:
            print("ERROR: data is not a tuple!") if VERBOSE else None
            print(f'data type received: {type(data)}') if VERBOSE else None
            print(f'data received: {data}') if VERBOSE else None
            logging.error(f"ERROR: data is not a tuple! data type received: {type(data)}")
            return None,None # return empty lists
        
        # check if the tuple has 2 items, and if the first item is a dict, and the second is a np.array
        if len(data) != 2 or type(data[0]) != dict or type(data[1]) != np.ndarray:
            print("ERROR: data tuple is not the correct format!") if VERBOSE else None
            print(f'data tuple received: {data}') if VERBOSE else None
            logging.error(f"ERROR: data tuple is not the correct format! data tuple received: {data}")
            return None,None # return empty lists

        additional_info = data[0] # dict
        data = data[1] # np.array

        return additional_info, data
    # ======================================================================== CALL FUNCTIONS
    def send_floats(self, float_list:List[float]) -> None:
        '''send a float data message as a 'blob' pair to the transceiver'''
        if len(float_list) > 375: # check if the data is too large for a single message
            print("ERROR: data is too large for a single message!") # datalink layer should handle this
            logging.error("ERROR: data is too large for a single message!")
            # float_list = float_list[:375] # we clip the data to the first 375 elements
        pdu = pmt.init_f32vector(len(float_list), float_list) # create a pmt vector
        pair = pmt.cons(pmt.PMT_NIL, pdu) # create a pmt pair (no symbol needed so PMT_NIL)
        # print(f'pair? {pmt.is_pair(pair)}')
        msg = pmt.serialize_str(pair)
        # self.sent_data.append((float_list, msg))  # save the sent data for tracking
        self.tx_socket.send(msg)

    def send_at(self, float_list:List[float], target_ms:int) -> int:
        '''send a float data message as a 'blob' pair to the transceiver
            send @ a specific timestamp (must be less that 5 seconds in the future)'''
        now = int(time.time()*1000) # in milliseconds
        #check if the input timestamp is in the future and is less than 5 seconds in the future
        if target_ms < now: 
            delay = now - target_ms
            print(f"ERROR: timestamp is not in the future! {delay} ms") if VERBOSE else None
            logging.error(f"ERROR: timestamp is not in the future! {delay} ms")
            # we just send the data without waiting
            self.send_floats(float_list)
            self.underrun += 1 # count the underrun
            return now
        elif target_ms > now + 5000:
            print("ERROR: timestamp is more than 5 seconds in the future!") if VERBOSE else None
            logging.error("ERROR: timestamp is more than 5 seconds in the future!")
            # we just send the data without waiting
            self.send_floats(float_list)
            return now
        else: # we wait until the timestamp to send the data
            delay = target_ms - now
            if delay > 1: # prevent negative delay
                time.sleep((delay - 1 )/1000) # delay in seconds, minus 1 ms
            # precise timing
            while now:=int(time.time()*1000) < target_ms:
                pass
            self.send_floats(float_list)
            return now

    def close(self):
        self.tx_socket.close()
        self.rx_socket.close()
        self.context.term()
        print("Transceiver sockets closed") if VERBOSE else None
        logging.info("Transceiver sockets closed")
    
    def receive_floats(self, timeout:int=1000) -> tuple:
        '''receive a float data message as a 'blob' pair from the transceiver'''
        if self.rx_socket.poll(timeout, zmq.POLLIN) == 0:
            return None, None
        msg = self.rx_socket.recv()
        additional_msg, msg = self._decode_PMT(msg)
        # self.received_data.append((additional_msg,msg))
        return additional_msg, msg
    
    def parse_mac(self, msg:dict):
        '''parse the message to get the mac address of the device'''
        if msg is None:
            return None, None
        # the data list with a dictionary, the mac addresses as keys (address1, address2)
        try:
            dest_mac,tx_mac = msg['address 1'], msg['address 2']
        except KeyError:
            print("ERROR: could not parse mac addresses!") if VERBOSE else None
            logging.error("ERROR: could not parse mac addresses!")
            return None, None
        return dest_mac, tx_mac
    
    def parse_seq_num(self, msg:dict):
        '''parse the message to get the sequence number of the message'''
        if msg is None:
            return None
        try:
            seq_num = msg['sequence number']
        except KeyError:
            print("ERROR: could not parse sequence number!") if VERBOSE else None
            logging.error("ERROR: could not parse sequence number!")
            return None
        return seq_num
    
# =============================================================================================== MAIN    
if __name__ == "__main__":
    address = "127.0.0.1"
    tx_port = 50010
    rx_port = 50011

    # list of sequence numbers
    seq = 0
    tx_seq = [] 
    rx_seq = []

    # TX_EVERY = 120 # milliseconds
    # RX_POLL_DELAY = 20 # milliseconds to wait before polling for received data
    # RX_POLL_TIMEOUT = 90 # milliseconds to wait for received data

    TX_EVERY = 10 #22 #50 # milliseconds
    RX_POLL_DELAY = 1 #10 # milliseconds to wait before polling for received data
    RX_POLL_TIMEOUT = 2 #10 # milliseconds to wait for received data
    
    print("running as main")
    logging.info("running as main")
    print('connecting')
    logging.info('connecting')
    txrx = transceiver(address, tx_port, rx_port)
    print('connected')
    logging.info('connected')
    logging.info(f'address: {address}')
    logging.info(f'tx_port: {tx_port}')
    logging.info(f'rx_port: {rx_port}')
    logging.info(f'TX_EVERY: {TX_EVERY}')
    logging.info(f'RX_POLL_DELAY: {RX_POLL_DELAY}')
    logging.info(f'RX_POLL_TIMEOUT: {RX_POLL_TIMEOUT}')
    start_time = time.time()
    next_send_time = int(time.time()*1000) + TX_EVERY
    try:
        while len(tx_seq) < 800:
            msg = [-1.1802468879641618e+29]*375 # floating DEADBEEF! (375 floats is max for BPSK)
            print(f"message: {msg}") if VERBOSE else None
            print(f"message type: {type(msg[0])}") if VERBOSE else None
            logging.info(f"time now (ms): {int(time.time() * 1000)}")
            logging.info(f"waiting for next send time: {next_send_time}")
            txrx.send_at(msg, next_send_time) # BLOCKING!!
            next_send_time += TX_EVERY
            print(f"Sent message @ {now}") if VERBOSE else None
            tx_seq.append(seq); seq += 1

            logging.info(f"Sent message")
            logging.info(f'Sent datatype: {type(msg)}')
            logging.info(f'Sent length: {len(msg)}')
            logging.info(msg)

            time.sleep(RX_POLL_DELAY/1000) # delay to wait for tx to finish

            rx_timer = int(time.time()*1000)
            additional_data, data = txrx.receive_floats(timeout=RX_POLL_TIMEOUT) # BLOCKS for timeout
            logging.info(f"finished rx poll, time now (ms): {int(time.time() * 1000)}")
            # log the time taken to poll for a receive message
            logging.info(f"rx poll time: {int(time.time()*1000) - rx_timer} ms")

            if data is None:
                print("No data received") if VERBOSE else None
                logging.info("No data received")
            else:
                now = int(time.time())
                print(f"Received message @ {now}") if VERBOSE else None
                # print(f'Received datatype: {type(data)}')
                # print(f'Received length: {len(data)}')
                logging.info(f"Received message")
                logging.info(f'Received datatype: {type(data)}')
                logging.info(f'Received length: {len(data)}')
                logging.info(f'Received message: {data}')

                # print(data)
                # check divisor for 32 bit float, should be 4, and print as float
                if len(data)%4 != 0: # cannot convert to float
                    print("WARNING: data length is not divisible by 4!") if VERBOSE else None
                    logging.warning("WARNING: data length is not divisible by 4!?")
                    rx_seq.append("INV") # invalid packet
                elif len(data) < 1528: # the packet size is smaller than a full packet (BPSK)
                    print("WARNING: data length is less than 1528!") if VERBOSE else None
                    logging.warning("WARNING: data length is less than 1528!?")
                    rx_seq.append("SML") # invalid packet
                else: # assume a valid packet
                    print(f'as float: {data.view(np.float32)}') if VERBOSE else None # print as float
                    logging.info(f'Received as float: {data.view(np.float32)}')
                    # grab the sequence number
                    seq_num = txrx.parse_seq_num(additional_data)
                    rx_seq.append(seq_num) #if seq_num is not None else None
                    print(f'seq_num: {seq_num}') if VERBOSE else None

                    # print(f'Received as hex: {[' '.join(f'{hex_value:02x}') for hex_value in data ]}') # print as hex
                    logging.info(f'Received as hex: {[' '.join(f'{hex_value:02x}') for hex_value in data ]}')

                    # print(f'Received additional datatype: {type(additional_data)}')
                    # print(additional_data)
                    logging.info(f'Received additional datatype: {type(additional_data)}')
                    logging.info(additional_data)

                # grab mac info
                dest_mac, tx_mac = txrx.parse_mac(additional_data)
                print(f'dest_mac: {dest_mac}') if VERBOSE else None
                print(f'tx_mac: {tx_mac}') if VERBOSE else None
                logging.info(f'dest_mac: {dest_mac}')
                logging.info(f'tx_mac: {tx_mac}')
            # print the session summary every X seconds
            # if int(time.time()) % 5 == 0:
            #     print(f'session summary: \n'
            #         f'num rx: {len(rx_seq)} \n'
            #         f'num tx: {len(tx_seq)} \n'
            #         f'tx seq num: {tx_seq} \n'
            #         f'rx seq num: {rx_seq} \n\n'
            #         )
            logging.info(f'loop iteration complete {time.time()*1000} ms\n')
        

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        txrx.close()
        print("Transceiver closed")
        logging.info("Transceiver closed")
        run_time = time.time() - start_time
        # get the dropped packets
        dropped_packets = [x for x in tx_seq if x not in rx_seq]
        percent_dropped = len(dropped_packets)/len(tx_seq)*100
        inv_packets = [x for x in rx_seq if x == 'INV']
        sml_packets = [x for x in rx_seq if x == 'SML']
        # print the session summary
        logging.info(f'session summary: \n'
                    f'num rx: {len(rx_seq)} \n'
                    f'num tx: {len(tx_seq)} \n'
                    f'tx seq num: {tx_seq} \n'
                    f'rx seq num: {rx_seq} \n'
                    f'dropped packets: {dropped_packets} \n'
                    f'packet loss: {len(dropped_packets)} of {len(tx_seq)} \n'
                    f'percent loss: {percent_dropped:.2f}% \n'
                    f'underruns: {txrx.underrun} \n'
                    f'invalid packets: {len(inv_packets)} \n'
                    f'small packets: {len(sml_packets)} \n'
                    f'run time: {run_time:.2f} seconds\n'
                    )
        print(f'session summary: \n'
                    f'num rx: {len(rx_seq)} \n'
                    f'num tx: {len(tx_seq)} \n'
                    f'tx seq num: {tx_seq} \n\n'
                    f'rx seq num: {rx_seq} \n\n'
                    f'dropped packets: {dropped_packets}\n\n'
                    f'packet loss: {len(dropped_packets)} of {len(tx_seq)} \n'
                    f'percent loss: {percent_dropped:.2f}% \n'
                    f'underruns: {txrx.underrun} \n'
                    f'invalid packets: {len(inv_packets)} \n'
                    f'small packets: {len(sml_packets)} \n'
                    f'run time: {run_time:.2f} seconds\n'
                    )
        
# =============================================================================================== END
# from here we can see that many packets are dropped and packet level handling is needed
