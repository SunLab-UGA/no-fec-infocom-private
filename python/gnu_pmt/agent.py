# this holds the class which is used to receive, train and transmit the model
# forgo the .env file (no time to implement it)
# use args to know what action to take


import zmq
import time
import pmt
import numpy as np
from typing import List, Callable

from fed_model.client import MnistClient
from fed_model.server import MnistServer, compare_models, compare_flattened_parameters
from fed_model.central_model import MnistModel

from trans import transceiver

from datetime import datetime
import logging
import glob
import subprocess
import argparse
import logging
import os
import fcntl


# windows tip: shift-alt-a does a block comment

class Agent: # this can be a client_agent or a server_agent
    def __init__(self, seed=0):
        """ initialize the agent """
        self.seed = seed
        self.whoami = 'agent'
        self.model = MnistModel()
        self.client = MnistClient(self.model, seed=self.seed)

        self.subprocess_running = False # track the subprocess
        self.transceiver_running = False # track the transceiver
    def start_transceiver(self): # ==================================start_transceiver
        """ start the transceiver """
        self.txrx = transceiver("127.0.0.1",50010, 50011)
        self.transceiver_running = True
    def set_whoami(self, whoami):
        """ check if the agent is a client or a server """
        valid = ['client0', 'client1', 'server']
        if whoami not in valid:
            raise ValueError(f'Invalid agent type: {whoami}')
        self.whoami = whoami
    def start_subprocess(self, script_name: str): # ===================start_subprocess
        """ start the subprocess GNU Radio"""
        self.process = subprocess.Popen(['python', script_name],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                        text=True)
        self.subprocess_running = True 
    def set_non_blocking(self,fd): # make the stdout non-blocking
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    def read_from_pipe(self,fd): # read from the pipe
        try:
            return os.read(fd, 4096).decode()
        except BlockingIOError:
            return '' # no data
    def check_subprocess(self):
        """ check if the subprocess is running """
        if not self.subprocess_running:
            return False # maybe didn't start the subprocess yet
        if self.process.poll() is None:
            self.subprocess_running = True
            return True
        else:
            logging.error('Subprocess has stopped')
            self.subprocess_running = False
            std_out, std_err = self.process.communicate()
            if std_out:
                logging.error(f'stdout: {std_out}')
            if std_err:
                logging.error(f'stderr: {std_err}')
    def communicate_subprocess(self):
        """ communicate with the subprocess """
        if not self.subprocess_running:
            logging.error('Subprocess is not running')
            raise ValueError('Subprocess is not running')
        std_out, std_err = self.process.communicate()
        if std_out:
            logging.info(f'stdout: {std_out}')
        if std_err:
            logging.error(f'stderr: {std_err}')
    def stop_subprocess(self):
        """ stop the subprocess """
        if not self.subprocess_running:
            logging.info('Subprocess cannot be stopped, was not running')
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=1)
            logging.info('Subprocess terminated')
        except subprocess.TimeoutExpired:
            self.process.kill() # with fire this time
            self.process.wait(timeout=1)
            logging.info('Subprocess killed')
        finally:
            self.subprocess_running = False
    def train(self): # =====================================train
        """ locate the newest server model file, load and train it 
        and save the model. If no model found, a base model is used."""
        self.client.load_server_model()
        self.client.fit() # auto 1 epoch
        filename = f'{self.whoami}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pth'
        self.client.save_model_dict(path=filename)
    def transmit(self): # ==================================transmit (BLOCKING!)
        """ transmit the model to the server """
        # check if the transceiver is running
        if not self.transceiver_running:
            logging.error('Transceiver is not running')
            raise ValueError('Transceiver is not running, start_subprocess()')
        # load the newest model, find it first by glob
        try:
            newest_model = max(glob.iglob(f'{self.whoami}_*.pth'), key=os.path.getctime)
        except ValueError:
            logging.error('No model found')
            self.stop_subprocess() # stop the subprocess
            raise ValueError('No model found')
        self.client.load_model_dict(newest_model)
        # get the flattened model
        flat = self.client.get_flattened_parameters()
        self.txrx.transmit_flattened_model(flattened_parameters=flat)
    def receive(self, who_tx: str = None): # ==================================receive (BLOCKING!)
        """ receive the model from the client """
        # check if the transceiver is running
        if not self.transceiver_running:
            logging.error('Transceiver is not running')
            raise ValueError('Transceiver is not running, start_subprocess()')
        # receive the model
        flat = self.txrx.receive_flattened_model()
        if flat is None:
            logging.error('No model received')
            self.stop_subprocess() # stop the subprocess
            raise ValueError('No model received')
        self.client.set_flattened_parameters(flat)
        # save the model
        if self.whoami == 'client0' or self.whoami == 'client1':
            filename = f'server_{datetime.now().strftime("%Y%m%d%H%M%S")}.pth'
        elif self.whoami == 'server': # save the client model, care no check
            filename = f'{who_tx}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pth'
        self.client.save_model_dict(path=filename)
    def txrx_at_time(self, UTC_time_ms: int, action: Callable[[], any]):
        """ transmit or receive at a specific time """
        now = int(time.time()*1000) # in milliseconds
        #check if the input timestamp is in the future and is less than 5 seconds in the future
        if UTC_time_ms < now: 
            delay = now - UTC_time_ms
            logging.error(f"ERROR: timestamp is not in the future! {delay} ms")
            # we just send the data without waiting 
            return action()
        elif UTC_time_ms > now + 5000:
            logging.error("ERROR: timestamp is more than 5 seconds in the future!")
            # we just send the data without waiting
            return action()
        else: # we wait until the timestamp to send the data
            delay = UTC_time_ms - now
            if delay > 1: # prevent negative delay
                time.sleep((delay - 1 )/1000) # delay in seconds, minus 1 ms
            # precise timing
            while now:=int(time.time()*1000) < UTC_time_ms:
                pass
            return action()
    # ============================================================================= server functions (server_agent)
    def federate(self): # ==================================init_server
        """ federate the models from the clients. Assumes the models are already saved."""
        logging.info('Federating models...')
        # load the client models
        clients:list[MnistClient] = []; client_weights = [] # list of clients and their flattened_weights
        newest_model0 = max(glob.iglob(f'client0_*.pth'), key=os.path.getctime)
        newest_model1 = max(glob.iglob(f'client1_*.pth'), key=os.path.getctime)
        for i, model in enumerate([newest_model0, newest_model1]):
            if not model:
                logging.error(f'model{i} not found')
                self.stop_subprocess() # stop the subprocess
                raise ValueError(f'model{i} not found')
            logging.info(f'loading model {model}')
            client = MnistClient(MnistModel())
            client.load_model_dict(model)
            clients.append(client)
            client_weights.append(client.get_flattened_parameters())
            logging.info(f'client{i} loaded')
        # sanity check, the client models should not be equal
        if compare_models(clients[0].model, clients[1].model):
            logging.error('Client models are equal')
            print('ERROR: Client models are equal and should not be')
            self.stop_subprocess() # stop the subprocess
            raise ValueError('Client models are equal')   
        # average the weights
        self.server = MnistServer(self.model)
        self.server.load_client_model(clients[0]) # wow this got out of hand...
        self.server.load_client_model(clients[1]) # anyway, we load the client models, as clients...
        avg_weights = self.server.fedavg()
        self.server.server.set_flattened_parameters(avg_weights)
        # evaluate the model
        acc = self.server.server.evaluate()
        logging.info(f'fed accuracy: {acc}')
        # save the model
        filename = f'server_{datetime.now().strftime("%Y%m%d%H%M%S")}.pth'
        self.server.server.save_model_dict(path=filename)
# ============================================================================= END agent

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Client or server agent')
    parser.add_argument('--whoami', type=str, help='client0, client1, or server')
    parser.add_argument('--action', type=str, help='train, transmit, receive, federate') # federate is for the server
    parser.add_argument('--from_who', type=str, help='receive from [client0, client1]', default=None) # only for server
    parser.add_argument('--time', type=int, help='time to transmit or receive')
    parser.add_argument('--seed', type=int, help='random seed', default=0)
    args = parser.parse_args()

    # setup logging
    time_suffix = time.strftime("%Y%m%d-%H%M%S")
    logging.basicConfig(filename=f'application{time_suffix}.log',
                    filemode= 'w',
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
    logging.info(f'Agent started with {args=}')

    np.random.seed(int(args.seed))
    logging.info(f'Random seed set to {args.seed}')

    # get the time and perform the delay and rounding to the nearest second
    

    agent = Agent(seed=int(args.seed))
    agent.set_whoami(args.whoami)
    print(f'{agent.whoami=}')
    print(f'action: {args.action}')

    # start the subprocess (we do this even if we don't need it, consistency)
    # use glob to find the file path first!!! (must be local to this file!!!)
    try:
        name = 'wifi_transceiver_nogui.py'
        path = f"../../gnuradio_companion/{name}"
        txrx_file = next(glob.iglob(path), None)
        if txrx_file is None:
            logging.error(f'{name} not found @ {path}')
            agent.stop_subprocess() # stop the subprocess
            raise FileNotFoundError(f'{name} not found at {path}')
    except FileNotFoundError as e:
        logging.error(str(e))
        exit(1)

    print(f'{txrx_file=}')
    agent.start_subprocess(txrx_file)
    agent.set_non_blocking(agent.process.stdout.fileno())
    time.sleep(4.5) # wait for the radio to boot up (cold boot can take longer, beware!)
    print(f'{agent.check_subprocess()=}')
    std_out = agent.read_from_pipe(agent.process.stdout.fileno())
    err_out = agent.read_from_pipe(agent.process.stderr.fileno())
    logging.info(f'{std_out=}')
    logging.info(f'{err_out=}')

    # temporary testing
    # agent.stop_subprocess()
    # print(f'{agent.check_subprocess()=}')
    
    # start the transceiver
    if args.action == 'transmit' or args.action == 'receive':
        if not agent.subprocess_running:
            logging.error('Subprocess not running')
            exit(1)

        agent.start_transceiver()
        print(f'{agent.transceiver_running=}')

    if args.action == 'train':
        logging.info('Training model...')
        agent.train()
    elif args.action == 'transmit':
        if args.time:
            agent.txrx_at_time(args.time, agent.transmit)
    elif args.action == 'receive':
        if args.from_who is None:
            if args.time:
                agent.txrx_at_time(args.time, agent.receive)
        else: # only for server
            if args.time:
                agent.txrx_at_time(args.time, lambda: agent.receive(who_tx=args.from_who))
    elif args.action == 'federate':
        '''federate the models'''
        if args.whoami != 'server':
            logging.error('Only the server can federate the models')
            agent.stop_subprocess() # stop the subprocess
            exit(1)
        agent.federate()
    else:
        logging.error(f'Invalid action: {args.action}')
        agent.stop_subprocess() # stop the subprocess
        exit(1)

    # stop the subprocess
    agent.stop_subprocess()
    logging.info('end of program')
