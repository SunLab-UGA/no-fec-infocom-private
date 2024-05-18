# this is used to send and receive data from the transceiver via zmq and pmt messages
# to do this we set a time for each transceiver to send and another time to receive messages
# choose the slot every 2 seconds to send (only two transceivers) (60%2+timemode_tx)


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

def check_if_empty(data):
    if len(data) == 1 and data[0] == 0:
        return True
    else:
        return False

def decode_PMT(data:dict) -> tuple:
    '''Decode the data tuple from a PMT message
        data should be a tuple of (dict, np.array)'''
    try:
        data = pmt.deserialize_str(data) # deserialize the data
        data = pmt.to_python(data) # convert the data to a python object
    except Exception as e:
        print(f"ERROR: could not decode PMT message: {e}")
        logging.error(f"ERROR: could not decode PMT message: {e}")
        return None,None

    # check if the data is 'empty', if so raise a warning and return 0
    if check_if_empty(data) == True:
        print("WARNING: empty data packet received!")
        logging.warning("WARNING: empty data packet received!")
        return None,None # return empty lists

    # check if the the data is a tuple
    if type(data) != tuple:
        print("ERROR: data is not a tuple!")
        print(f'data type received: {type(data)}')
        print(f'data received: {data}')
        logging.error(f"ERROR: data is not a tuple! data type received: {type(data)}")
        return None,None # return empty lists
    
    # check if the tuple has 2 items, and if the first item is a dict, and the second is a np.array
    if len(data) != 2 or type(data[0]) != dict or type(data[1]) != np.ndarray:
        print("ERROR: data tuple is not the correct format!")
        print(f'data tuple received: {data}')
        logging.error(f"ERROR: data tuple is not the correct format! data tuple received: {data}")
        return None,None # return empty lists

    additional_info = data[0] # dict
    data = data[1] # np.array

    return additional_info, data

class transceiver:
    def __init__(self, address, tx_port, rx_port, timemod_tx=0):
        self.address = address
        self.tx_port = tx_port
        self.rx_port = rx_port
        
        self.context = zmq.Context()
        self.tx_socket = self.context.socket(zmq.PUSH)
        self.tx_socket.bind(f"tcp://{address}:{tx_port}")

        self.rx_socket = self.context.socket(zmq.PULL)
        self.rx_socket.connect(f"tcp://{address}:{rx_port}")
        
        self.tx_time = timemod_tx
        assert self.tx_time == 0 or self.tx_time == 1, "tx_time must be 0 or 1"

        self.received_data = []
        self.sent_data = []
        self.seq_num = []

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
       
        self.sent_data.append((float_list, msg))  # save the sent data for tracking

        self.tx_socket.send(msg)

    def close(self):
        self.tx_socket.close()
        self.rx_socket.close()
        self.context.term()
        print("Transceiver sockets closed")
        logging.info("Transceiver sockets closed")
    
    def receive_floats(self):
        '''receive a float data message as a 'blob' pair from the transceiver'''
        if self.rx_socket.poll(1000, zmq.POLLIN) == 0:
            return None, None
        msg = self.rx_socket.recv()
        additional_msg, msg = decode_PMT(msg)
        self.received_data.append((additional_msg,msg))
        return additional_msg, msg
    
    def parse_mac(self, msg:dict):
        '''parse the message to get the mac address of the device'''
        if msg is None:
            return None, None
        # the data list with a dictionary, the mac addresses as keys (address1, address2)
        try:
            dest_mac,tx_mac = msg['address 1'], msg['address 2']
        except KeyError:
            print("ERROR: could not parse mac addresses!")
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
            print("ERROR: could not parse sequence number!")
            logging.error("ERROR: could not parse sequence number!")
            return None
        return seq_num
    
# =============================================================================================== MAIN    
if __name__ == "__main__":
    address = "127.0.0.1"
    tx_port = 50010
    rx_port = 50011

    txrx = transceiver(address, tx_port, rx_port, timemod_tx=0)
    try:
        while True:
            # get the time in seconds
            now = int(time.time())
            if now%2+txrx.tx_time == 0: # send data every 2 seconds, odd or even
                #msg = [-3.4684338734436437e-10, 0.0, -2.533883866617792e-11, 0.0, -8346975.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                # create a message with the same float repeated 375 times
                msg = [-1.1802468879641618e+29]*375 # floating DEADBEEF!
                # print the floats as uint8
                # print(f"message: {msg}")
                # print(f"message type: {type(msg[0])}")
                txrx.send_floats(msg)
                print(f"Sent message @ {now}") if VERBOSE else None
                logging.info(f"Sent message")
                logging.info(f'Sent datatype: {type(msg)}')
                logging.info(f'Sent length: {len(msg)}')
                logging.info(msg)

            time.sleep(0.05) #0.25 # sleep for 0.5 seconds

            additional_data, data = txrx.receive_floats()
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
                if len(data)%4 != 0:
                    print("WARNING: data length is not divisible by 4!")
                    logging.warning("WARNING: data length is not divisible by 4!?")
                if len(data) < 1528: # the packet size is smaller than a full packet (BPSK)
                    print("WARNING: data length is less than 1528!")
                    logging.warning("WARNING: data length is less than 1528!?")
                else:
                    # print(f'as float: {data.view(np.float32)}') # print as float
                    logging.info(f'Received as float: {data.view(np.float32)}')

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

                # grab the sequence number
                seq_num = txrx.parse_seq_num(additional_data)
                print(f'seq_num: {seq_num}') if VERBOSE else None
                txrx.seq_num.append(seq_num)
            
            # print the session summary every X seconds
            if now%5 == 0:
                print()
                print(f'session summary: \n'
                    f'num rx: {len(txrx.received_data)} \n'
                    f'num tx: {len(txrx.sent_data)} \n'
                    f'seq num: {txrx.seq_num} \n'
                    )
                # filter the sequence numbers (remove any none sequences and None values)
                seq_num = [x for x in txrx.seq_num if x is not None] # remove None values
                print()

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        txrx.close()
        print("Transceiver closed")
        logging.info("Transceiver closed")
        # print the session summary
        logging.info(f'session summary: \n'
                  f'num rx: {len(txrx.received_data)} \n'
                  f'num tx: {len(txrx.sent_data)} \n'
                  f'seq num: {txrx.seq_num} \n'
                  )
