# this is used to send and receive data from the transceiver via zmq and pmt messages
# to do this we set a time for each transciever to send and another time to receive messages
# choose the slot every 2 seconds to send (only two transceivers) (60%2+timemode_tx)

# this code has an issue with the pmt message decoding, it is not able to decode the message


import zmq
import time
import pmt
import numpy as np
import struct
import ctypes
from typing import List

# address = "127.0.0.1"
# tx_port = 50010
# rx_port = 50011

def check_if_empty(data):
    if len(data) == 1 and data[0] == 0:
        return True
    else:
        return False

def decode_PMT(data:pmt) -> tuple:
    '''Decode the data tuple from a PMT message
        data should be a tuple of (dict, np.array)'''
    
    data = pmt.deserialize_str(data) # deserialize the data
    data = pmt.to_python(data) # convert the data to a python object

    # check if the data is 'empty', if so raise a warning and return 0
    if check_if_empty(data) == True:
        print("WARNING: empty data packet recieved!")
        return ([],[]) # return empty lists

    # check if the the data is a tuple
    if type(data) != tuple:
        print("ERROR: data is not a tuple!")
        return ([],[]) # return empty lists
    
    # check if the tuple has 2 items, and if the first item is a dict, and the second is a np.array
    if len(data) != 2 or type(data[0]) != dict or type(data[1]) != np.ndarray:
        print("ERROR: data tuple is not the correct format!")
        return ([],[]) # return empty lists

    additional_info = data[0] # dict
    data = data[1] # np.array

    return additional_info, data


class tranceiver:
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

        self.recieved_data = []

    # def send(self, data:str):
    #     '''send a string data message to the tranceiver'''
    #     msg = pmt.to_pmt(data) # <class 'pmt.pmt_python.pmt_base'>
    #     msg = pmt.serialize_str(msg) # <class 'bytes'>
    #     self.tx_socket.send(msg) # default message socket

    # def send_float_blob(self, float_list:List[float]) -> None:
    #     '''send a float data message as a 'blob' to the tranceiver'''
    #     binary_data = struct.pack(f'{len(float_list)}f', *float_list)
    #     c_buffer = ctypes.create_string_buffer(binary_data)
    #     msg = pmt.make_blob(ctypes.addressof(c_buffer), len(binary_data))
    #     msg = pmt.serialize_str(msg) 
    #     self.tx_socket.send(msg)

    def send_floats(self, float_list:List[float]) -> None:
        '''send a float data message as a 'blob' pair to the tranceiver'''
        pdu = pmt.init_f32vector(len(float_list), float_list) # create a pmt vector
        pair = pmt.cons(pmt.PMT_NIL, pdu) # create a pmt pair (no symbol needed so PMT_NIL)
        print(f'pair? {pmt.is_pair(pair)}')
        msg = pmt.serialize_str(pair)
        self.tx_socket.send(msg)

    def close(self):
        self.tx_socket.close()
        self.rx_socket.close()
        self.context.term()
        print("Tranceiver sockets closed")

    # def recieve(self):
    #     if self.rx_socket.poll(1000, zmq.POLLIN) == 0:
    #         return None
    #     msg = self.rx_socket.recv()
    #     msg = pmt.deserialize_str(msg)
    #     self.recieved_data.append(msg)
    #     return msg
    
    def recieve_floats(self):
        '''recieve a float data message as a 'blob' pair from the tranceiver'''
        if self.rx_socket.poll(1000, zmq.POLLIN) == 0:
            return None
        msg = self.rx_socket.recv()
        additional_msg, msg = decode_PMT(msg)
        return additional_msg, msg
    
    def parse_mac(self, msg=None):
        '''parse the message to get the mac address of the device,
        if the message is not provided, the last message recieved is used'''
        if msg is None:
            if len(self.recieved_data) == 0: # no history of messages
                return None, None
            additional_msg, msg = decode_PMT(self.recieved_data[-1]) # get the last message
        else:
            additional_msg, msg = decode_PMT(msg)

        # the data list with a dictionary, the mac addresses as keys (address1, address2)
        dest_mac,tx_mac = additional_msg['address 1'], additional_msg['address 2']
        return dest_mac, tx_mac
    
if __name__ == "__main__":
    address = "127.0.0.1"
    tx_port = 50010
    rx_port = 50011

    txrx = tranceiver(address, tx_port, rx_port, timemod_tx=0)
    try:
        while True:
            # get the time in seconds
            now = int(time.time())
            if now%2+txrx.tx_time == 0: # send data every 2 seconds, odd or even
                # msg = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                msg = [-3.4684338734436437e-10, 0.0, -2.533883866617792e-11, 0.0, -8346975.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                # print the floats as uint8
                print(f"message: {msg}")
                print(f'as uint8: {msg.view(np.uint8)}')
                txrx.send_floats(msg)
                print(f"Sent message @ {now}")
            time.sleep(0.5) # sleep for 0.5 seconds
            data = txrx.recieve_floats()
            print(f'datatype: {type(data)}')
            print(data)

            print()
            # print(txrx.parse_mac()) # has an error (string decoding...prolly because of the pmt message being floats?)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        txrx.close()
        print("Tranceiver closed")
