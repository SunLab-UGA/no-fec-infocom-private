# from tdm_trans.py we transmit and receive a model file
# client0_model_20240424181155.pth

import zmq
import time
import pmt
import numpy as np
from typing import List
import logging

from fed_model.client import MnistClient
from fed_model.server import MnistServer, compare_models, compare_flattened_parameters
from fed_model.central_model import MnistModel

from tdm_trans import transceiver

from datetime import datetime
import logging
import glob


time_suffix = time.strftime("%Y%m%d-%H%M%S")
logging.basicConfig(filename=f'model_txrx_{time_suffix}.log',
                filemode= 'w',
                format='%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level=logging.INFO)
# print statement verbosity
VERBOSE = False

# get the .pth model file
files = sorted(glob.glob(f'client0_model_*.pth'))
if len(files) == 0:
    raise FileNotFoundError('No model file found')
model_file = files[-1]
print(f'Using model file: {model_file}')

# make a client (who holds the model)
client = MnistClient(MnistModel(), seed=0)

# load the model from the file
client.load_model_dict(model_file)
logging.info(f'Loaded model from {model_file}')
# get the flattened parameters (this is what we will transmit)
flattened_parameters = client.get_flattened_parameters()

print(f'len(flattened_parameters): {len(flattened_parameters)}')
logging.info(f'len(flattened_parameters): {len(flattened_parameters)}')
logging.info(f'flattened_parameters: {flattened_parameters}')
# make a transceiver
address = "127.0.0.1"
tx_port = 50010
rx_port = 50011
txrx = transceiver(address, tx_port, rx_port)
print('connected')

TX_EVERY = 4 #10 #22 #50 # milliseconds
RX_POLL_DELAY = 0 #10 # milliseconds to wait before polling for received data
RX_POLL_TIMEOUT = 2 #10 # milliseconds to wait for received data
logging.info('connected')
logging.info(f'address: {address}')
logging.info(f'tx_port: {tx_port}')
logging.info(f'rx_port: {rx_port}')
logging.info(f'TX_EVERY: {TX_EVERY}')
logging.info(f'RX_POLL_DELAY: {RX_POLL_DELAY}')
logging.info(f'RX_POLL_TIMEOUT: {RX_POLL_TIMEOUT}')

# print the number of packets to transmit rounded up
floats_per_packet = 375 # 1500 bytes@bpsk, 4 bytes per float
num_packets = int(np.ceil(len(flattened_parameters) / floats_per_packet))

# create a packet array
pkts = np.zeros((num_packets, floats_per_packet))

for i in range(num_packets): # copy the flattened parameters into the packets
    pkts[i, :len(flattened_parameters[i*floats_per_packet:(i+1)*floats_per_packet])] = \
        flattened_parameters[i*floats_per_packet:(i+1)*floats_per_packet]

start_time = time.time()
next_send_time = int(time.time()*1000) + TX_EVERY
tx_seq = [] ; seq=0 # sequence number tracking
rx_seq = []

print(f'Transmitting {num_packets} packets')
try:
    for pkt in pkts:
        # transmit
        msg = []
        for i in range(len(pkt)):
            msg.append(pkt[i])
        logging.info(f'Sending data')
        logging.info(f'len(msg): {len(msg)}')
        logging.info(f'msg: {msg}')
        txrx.send_at(msg, next_send_time) # BLOCKING!!
        next_send_time += TX_EVERY
        tx_seq.append(seq); seq += 1 # sequence number tracking
        # tx_seq.append(seq); seq += 1
        time.sleep(RX_POLL_DELAY/1000) 
        # receive
        additional_data, data = txrx.receive_floats(timeout=RX_POLL_TIMEOUT) # BLOCKS for at most RX_POLL_TIMEOUT

        # parse the received message (if any)
        if data is None:
            logging.info('No data received')
        else:
            logging.info(f'Received data')
            logging.info(f'len(data): {len(data)}')
            logging.info(f'data: {data}')

            # parse validity
            if len(data)%4 != 0: # cannot convert to float
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
                rx_seq.append(seq_num)
                logging.info(f'Received as hex: {[' '.join(f'{hex_value:02x}') for hex_value in data ]}')
                logging.info(f'Received additional datatype: {type(additional_data)}')
                logging.info(additional_data)

            # parse the additional data (if any)
            dest_mac, tx_mac = txrx.parse_mac(additional_data)
            logging.info(f'dest_mac: {dest_mac}')
            logging.info(f'tx_mac: {tx_mac}')

except Exception as e:
    print(f"Exception: {e}")
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
                # f'tx seq num: {tx_seq} \n\n' # we know...
                f'rx seq num: {rx_seq} \n\n'
                f'dropped packets: {dropped_packets}\n\n'
                f'packet loss: {len(dropped_packets)} of {len(tx_seq)} \n'
                f'percent loss: {percent_dropped:.2f}% \n'
                f'underruns: {txrx.underrun} \n'
                f'invalid packets: {len(inv_packets)} \n'
                f'small packets: {len(sml_packets)} \n'
                f'run time: {run_time:.2f} seconds\n'
                )
    
# use received packets to reconstruct the flattened model and save it
