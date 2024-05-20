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
logging.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==============================================================================CONSTANTS
# print statement verbosity
VERBOSE = False
OVERRIDE_FLATTENED_PARAMETERS = True # override tx parameters with a known value for testing

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

#### OVERRIDE the flattened parameters with a known value for testing
if OVERRIDE_FLATTENED_PARAMETERS:
    flattened_parameters = np.ones_like(flattened_parameters) * -1.1802468879641618e+29 # fp32 0xDEADBEEF
    logging.info(f'Overriding flattened_parameters with a known value for testing')
    logging.info(f'flattened_parameters: {flattened_parameters}')

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
floats_per_packet = 375 # max1500 bytes@bpsk, 4 bytes per float
# floats_per_packet = 750 # max1500 bytes@qpsk, 4 bytes per float ? forgot why...
num_packets = int(np.ceil(len(flattened_parameters) / floats_per_packet))
logging.info(f'floats_per_packet: {floats_per_packet}')
logging.info(f'num_packets per model tx: {num_packets}')

# create a packet array
pkts = np.zeros((num_packets, floats_per_packet))

for i in range(num_packets): # copy the flattened parameters into the packets
    pkts[i, :len(flattened_parameters[i*floats_per_packet:(i+1)*floats_per_packet])] = \
        flattened_parameters[i*floats_per_packet:(i+1)*floats_per_packet]
    
# give a multiple of the packets for dropped packets
m = 10 #5
extended_pkts = np.tile(pkts, (m,1))
print(f'pkts.shape: {pkts.shape}')
logging.info(f'pkts.shape: {pkts.shape}')
print(f'extended_pkts.shape: {extended_pkts.shape}')
logging.info(f'extended_pkts.shape: {extended_pkts.shape}')
logging.info(f"repeating model transmit {m} times")

start_time = time.time()
next_send_time = int(time.time()*1000) + TX_EVERY
tx_seq = [] ; seq=0 # sequence number tracking
rx_seq = [] ; seq_num = 0 # sequence number tracking for received packets

rx_pkt = []

print(f'Transmitting {num_packets}x{m} ({len(extended_pkts)}) packets')
logging.info(f'Transmitting {num_packets}x{m} ({len(extended_pkts)}) packets')
try:
    # for pkt in pkts:
    for pkt in extended_pkts:
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
            rx_pkt.append(None)
            rx_seq.append("None")
        else:
            logging.info(f'Received data')
            logging.info(f'len(data): {len(data)}')
            logging.info(f'data: {data}')

            # parse validity
            if len(data)%4 != 0: # cannot convert to float
                logging.warning("WARNING: data length is not divisible by 4!?")
                rx_seq.append("INV") # invalid packet
                rx_pkt.append(None)
            elif len(data) < 1528: # the packet size is smaller than a full packet (BPSK)
                print("WARNING: data length is less than 1528!") if VERBOSE else None
                logging.warning("WARNING: data length is less than 1528!?")
                rx_seq.append("SML") # invalid packet
                rx_pkt.append(None)
            else: # assume a valid packet
                # grab the sequence number
                # seq_num = txrx.parse_seq_num(additional_data)
                rx_seq.append(seq_num) ; seq_num += 1
                logging.info(f'Received seq_num: {seq_num}')
                rx_pkt.append(data)
                print(f'as float: {data.view(np.float32)}') if VERBOSE else None # print as float
                logging.info(f'Received as float: {data.view(np.float32)}')
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
                f'num rx: {seq_num} \n'
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
                # f'rx seq num: {rx_seq} \n\n'
                # f'dropped packets: {dropped_packets}\n\n'
                f'packet loss: {len(dropped_packets)} of {len(tx_seq)} \n'
                f'percent loss: {percent_dropped:.2f}% \n'
                f'underruns: {txrx.underrun} \n'
                f'invalid packets: {len(inv_packets)} \n'
                f'small packets: {len(sml_packets)} \n'
                f'run time: {run_time:.2f} seconds\n'
                )
    
# use received packets to reconstruct the flattened model and save it
logging.info("TX/RX Finished")
print("TX/RX Finished")

#check for any missing packets (split and check for double dropped pkts)
def compare_string_indices_divided(rx_list, times_sent):
    dropped_packets = []
    success_packets = []
    # Calculate the length of each segment
    segment_length = len(rx_list) // times_sent
    segments = [rx_list[i * segment_length:(i + 1) * segment_length] for i in range(times_sent)]

    logging.info(f'segment ind: {"\t".join([str(x) for x in range(segment_length)])}') # log the segment indices (QOL)
    for i, segment in enumerate(segments): # log the segments
        logging.info(f'segment {i}:\t {"\t".join([str(s) for s in segment])}')

    # Check if the segments have the same string at any specific index
    for index in range(segment_length):
        # Collect elements at the current index from each segment if they are strings
        drops = [segment[index] for segment in segments if isinstance(segment[index], str)] # indicates dropped packets
        success = [segment[index] for segment in segments if isinstance(segment[index], int)]
        # Check if all elements are the same and there's at least one element
        if len(drops) == times_sent:
            dropped_packets.append(index)
        else:
            # give the first element which is not a string
            success_packets.append(success[0])
    # logging
    logging.info(f'segment ind: {"\t".join([str(x) for x in range(segment_length)])}') # QOL
    logging.info(f'success_packets: {"\t".join([str(s) for s in success_packets])}') #  check the success packets
    return dropped_packets, success_packets

dropped_packets_indexes, success_packets_indexes = compare_string_indices_divided(rx_seq, m)
logging.info(f"Dropped packet at index: {dropped_packets_indexes}")
logging.info(f'len(rx_seq): {len(rx_seq)}')
print(f"Dropped packet at index: {dropped_packets_indexes}")
print(f'len(dropped_packets): {len(dropped_packets_indexes)}')

# reconstruct the model from the received packets
if len(dropped_packets_indexes) > 0:
    print('Model reconstruction failed')
    logging.info('Model reconstruction failed')
    exit()

# use the success packets indexes to complete the model reconstruction (got cornered a bit here...)
# we should really be using the transceiver class to handle these operations
# build ANOTHER index
index_list = []
for i in range(len(success_packets_indexes)):
    # find the index of the success packet
    search_for_index = success_packets_indexes[i]
    # find the index of the success packet in the rx_seq
    index = rx_seq.index(search_for_index)
    index_list.append(index)


success_packets = [rx_pkt[i] for i in index_list]
logging.info(f'len(success_packets): {len(success_packets)}')
logging.info(f'success_packets: {success_packets}')

def parse_rx_pkt(pkt: np.ndarray) -> np.ndarray:
    # convert the packet to a list of floats
    try:
        pkt = pkt.view(np.float32)
        pkt = np.nan_to_num(pkt) # convert any nan to zeros
    except Exception as e:
        logging.info(f'pkt: {pkt}')
        print(f'pkt: {pkt}')
        logging.info(f'Exception: {e}')
        exit()

    # remove the first 24 bytes (6 floats) which are the header
    pkt = pkt[6:]
    # remove the last 4 bytes (1 float) which are the footer (crc32)
    pkt = pkt[:-1]
    # return the rest of the packet as list of floats
    return pkt

# parse the received packets
logging.info(f'Parsing received packets')
rx_params = [parse_rx_pkt(pkt) for pkt in success_packets]
logging.info(f'rx_params shape: {np.shape(rx_params)}')
logging.info(f'len(rx_params): {len(rx_params)}')
rx_params = np.array(rx_params).reshape(-1) # flatten the list of lists
logging.info(f'rx_params shape (flat): {np.shape(rx_params)}')

params = np.zeros_like(flattened_parameters)
# copy the received parameters into the model
for i in range(len(flattened_parameters)):
    params[i] = rx_params[i] # this should strip the padding zeros from the end

logging.info(f'params: {params}')

# compare the received parameters with the original
same = compare_flattened_parameters(flattened_parameters, params)
logging.info(f'is the model the same? {same}')
print(f'is the model the same? {same}')

print('calculating stats')
np.set_printoptions(threshold=np.inf, linewidth=np.inf) # print the whole array without truncation
logging.info(f'flattened_parameters: {flattened_parameters}')
logging.info(f'params: {params}')

# show the max values of the parameters
logging.info(f'max(flattened_parameters): {np.max(flattened_parameters)}')
logging.info(f'max(params): {np.max(params)}')

# show the differences
diff = flattened_parameters - params
logging.info(f'diff: {diff}')

# get and log the max difference
max_diff = np.max(np.abs(diff))
logging.info(f'max_diff: {max_diff}')

if OVERRIDE_FLATTENED_PARAMETERS:
    # find the indexes which are different from the known value (-1.1802468879641618e+29)
    diff_indexes = np.where(-1.1802468879641618e+29 != params)
    logging.info(f'len(diff_indexes): {len(diff_indexes)}')
    logging.info(f'diff_indexes: {diff_indexes}')


# # get and log the number of differences
# num_diff = np.sum(np.abs(diff) > 1e-6)
# logging.info(f'num_diff > 1e-6: {num_diff} of {len(flattened_parameters)}')

# # get and log the number of differences
# num_diff = np.sum(np.abs(diff) > 1e-3)
# logging.info(f'num_diff > 1e-3: {num_diff} of {len(flattened_parameters)}')


print('Model reconstruction successful')
logging.info('Model reconstruction successful')

# logging.info(f'len(success_packets): {len(success_packets)}')
# logging.info(f'success_packets: {success_packets}')

# attempt to load the parameters
print('Loading model from received packets')
try:
    client.set_flattened_parameters(params)
    logging.info('Loaded model from received packets')
except Exception as e:
    print(f"Exception: {e}")
    logging.info(f'Exception: {e}')

# save the model
model_file = f'rx_client0_model_{time_suffix}.pth'
client.save_model_dict(model_file)
logging.info(f'Saved model to {model_file}')
print(f'Saved model to {model_file}')

# plot the differences?