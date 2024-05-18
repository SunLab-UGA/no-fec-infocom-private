# transmitter class
# used to flatten and transmit a "pth" pytorch saved model via GNU Radio zmq socket

import zmq
import pmt
import argparse

from dotenv import load_dotenv
import os

from fed_model.client import MnistClient
from fed_model.central_model import MnistModel

import logging
logging.basicConfig(filename='application.log', 
                filemode= 'a',
                format='%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level=logging.INFO)

# logging.basicConfig(filename='application.log',
#                 filemode= 'w',
#                 format='%(asctime)s - %(message)s',
#                 datefmt='%Y-%m-%d %H:%M:%S',
#                 level=logging.DEBUG)

def parse_dotenv(path: str = '.env'):
    '''parse and get the environment variables from a .env file'''
    env = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or line.startswith('\n'):
                continue
            k, v = line.split('=')
            env[k] = v
    return env

class transmitter:
    def __init__(self, fed_client: MnistClient, env_path: str = '.env'):
        self.client = fed_client

        env_loaded = load_dotenv(env_path) # load environment variables
        if not env_loaded:
            logging.error(f'Failed to load environment variables from {env_path}')
            raise ValueError('Failed to load environment variables')
        if logging.getLogger().isEnabledFor(logging.DEBUG): # print all if debug is enabled
            logging.debug('Environment variables loaded:')
            for k, v in os.environ.items():
                logging.debug(f'{k}: {v}')
        env_list = parse_dotenv(env_path).keys() # get the list of environment variables
        logging.info(f'Environment variables loaded: {env_list}')
        for env in env_list: # check if all environment variables are set
            if os.getenv(env) is None:
                raise ValueError(f"Environment variable {env} not found")
        # load the attributes from the environment variables
        for env in env_list:
            setattr(self, env, os.getenv(env))
            logging.info(f'{env}: {getattr(self, env)}')

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        rc = self.socket.bind(f"tcp://{self.tx_address}:{self.tx_port}")
        # check if the socket is bound
        if rc == -1:
            logging.error(f'Failed to bind socket to tcp://{self.tx_address}:{self.tx_port}')
            raise ValueError('Failed to bind socket')
        logging.info(f'Socket bound to tcp://{self.tx_address}:{self.tx_port}')

    def send_model(self, path: str):
        '''load a model from a path and send it via zmq socket'''
        # use the client to load the model from the path
        self.client.load_model_dict(path)
        # get flattened model parameters from the client
        model_params = self.client.get_flattened_parameters()
        # create a PMT object to send the model
        msg = pmt.to_pmt(model_params)
        msg = pmt.serialize_str(msg)
        self.socket.send(msg)
        logging.info(f'Model sent: {path}')
    
    def close(self):
        self.socket.close()
        self.context.term()
        logging.info('Socket closed')
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Transmit a model via zmq socket')
    parser.add_argument('--path', type=str, help='path to the model to transmit', default='model.pth')
    args = parser.parse_args()
    logging.info(f'Loading model at {args.path}')

    client = MnistClient(MnistModel(), seed=321)
    tx = transmitter(client)

    logging.info('Transmitting model')
    tx.send_model(args.path)
    tx.close()
    


