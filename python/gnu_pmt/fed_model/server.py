# this is a server that will run a federated learning example using the MNIST dataset

# The server will be responsible for aggregating the model updates from the clients
# and updating the global model.

# the server is essentially a "client" that has access to all the data, and can aggregate the updates

# Here we implement FEDAVG, which is a simple federated learning algorithm
# it is assmumed that the clients use the same number of data points, and the same batch size
# so that the averaging can be done simply by averaging the model parameters


import torch
import numpy as np

from fed_model.central_model import MnistModel, load_data, train, evaluate
from fed_model.client import MnistClient
from fed_model.noise import add_noise_to_array, add_noise_to_array_v2

import warnings


# # make a function to add noise to the mantissa of a np.float32
# def add_binary_noise(y:np.float32, noise:int) -> np.float32:
#     '''add noise to the mantissa of a np.float32'''
#     y_bin = y.view(np.int32) # get the bitwise representation
#     if noise > 23:
#         warnings.warn('noise should be less than 23 bits (the length of the mantissa) to avoid flipping the exponent bits or sign bit') 
#     # give a random mask of 1s and 0s the length of the noise
#     r_mask = np.random.randint(0, 2, noise)
#     mask = 0
#     for bit in r_mask:
#         mask = (mask << 1) | bit
    
#     y_new_bin = y_bin ^ mask # flip the lsb of the mantissa
#     y_new = y_new_bin.view(np.float32) # convert back to np.float32
#     return y_new

# # make a function that will add noise to arrays of np.float32
# def add_noise_to_array(arr:np.ndarray, noise:int) -> np.ndarray:
#     '''add noise to an array of np.float32'''
#     return np.array([add_binary_noise(x, noise) for x in arr])

# def add_noise_to_array_v2(arr:np.ndarray, noise:int, percent:float) -> np.ndarray:
#     '''add noise to arrays of np.float32
#     add noise to a percentage of the array'''
#     arr_len = len(arr)
#     noise_coeff = np.random.choice([0, 1], arr_len, p=[1-percent, percent])
#     print(f'{noise_coeff=}')
#     out = []
#     for i,x in enumerate(arr):
#         print(f'{i=}, {x=}, {noise_coeff[i]=}')
#         if noise_coeff[i] == 1:
#             print(f'adding noise to {x}')
#             out.append(add_binary_noise(x, noise))
#         else:
#             print(f'not adding noise to {x}')
#             out.append(x)
#     return np.array(out)

class MnistServer():
    '''A simple server for federated learning using the MNIST dataset'''
    def __init__(self, model: torch.nn.Module, seed:int=42) -> None:
        self.model = model
        self.server = MnistClient(model,seed=seed) # create a "client" from the server model
        self.seed = seed
        self.client_flattened_parameters = [] # list of client parameters

    def fedavg(self) -> np.ndarray:
        '''Federated Averaging from loaded client models'''
        avg = np.mean(self.client_flattened_parameters, axis=0)
        self.server.set_flattened_parameters(avg)
        return avg
    
    def fedavg_with_noise(self, noise: int = 4) -> np.ndarray:
        '''Federated Averaging with noise: 
        add noise to the client parameters before averaging'''
        noisy_parameters = [add_noise_to_array(parameters, noise) for parameters in self.client_flattened_parameters]
        avg = np.mean(noisy_parameters, axis=0) # same as fedavg
        self.server.set_flattened_parameters(avg)
        return avg
    
    # def fedavg_with_noise_v2(self, noise: int = 4, percent: float = 0.1) -> np.ndarray:
    #     '''Federated Averaging with noise: 
    #     add noise to a percentage of the client parameters before averaging'''
        
    #     # add noise to the parameters
    #     noisy_parameters = [add_noise_to_array_v2(parameters, noise, percent) for parameters in self.client_flattened_parameters]
    #     avg = np.mean(noisy_parameters, axis=0)
    #     self.server.set_flattened_parameters(avg)
    #     return avg

    # def fedavg(self, weight_updates: list[np.ndarray]) -> np.ndarray:
    #     '''Federated Averaging with a list of weight updates from the clients'''
    #     return np.mean(weight_updates, axis=0)
    
    # def fedavg_with_lr(self, weight_updates: list[np.ndarray], learning_rates: list[float]) -> np.ndarray:
    #     '''Federated Averaging with a weighted learning rate for each client'''
    #     # THIS FUNCTION IS NOT USED IN THE EXAMPLE!!!
    #     lrs = np.array(learning_rates) # convert to numpy array
    #     lrs_norm = lrs / lrs.sum() # normalize the learning rates
    #     avg = np.zeros_like(weight_updates[0]) # initialize the final average
    #     for i, update in enumerate(weight_updates):
    #         avg += lrs_norm[i] * update
    #     return avg
    
    def load_client_model(self, client:MnistClient) -> None:
        '''load the client model from a file and append the flattened parameters to the list'''
        self.client_flattened_parameters.append(client.get_flattened_parameters())

def compare_models(model1:MnistModel, model2:MnistModel) -> bool:
    '''
    compare two models, used for a sanity check to ensure models are not equal,
    since we are averaging the weights of the clients, the models should not be equal
    also, the client models should not be equal to the server model, the base model, or among themselves
    '''
    dict1 = model1.state_dict()
    dict2 = model2.state_dict()
    if dict1.keys() != dict2.keys():
        return False # the keys are not equal
    for key in dict1:
        if not torch.equal(dict1[key], dict2[key]):
            return False # the tensors are not equal
    return True

def compare_flattened_parameters(p1:np.ndarray, p2:np.ndarray) -> bool:
    '''compare two flattened parameters'''
    return np.array_equal(p1, p2)


# ============================================================================= MAIN
def main():
    print(f'** FL Server: MNIST Example **')
    print(f'starting server...')
    np.random.seed(255)
    num_clients = 2
    
    # load the model from the centralized example
    print('loading base model...')
    base_model = MnistModel()
    client_models = [MnistModel(), MnistModel()] # create a list of base models for the clients
    # evaluate the model
    server_as_client = MnistClient(base_model) # create a "client" from new server model
    print('evaluating model before averaging...')
    acc = server_as_client.evaluate()
    print(f'accuracy: {acc}')

    # load the saved models from the clients (for ease, we just make a list of client models)
    print('loading client models...')
    clients = [MnistClient(client_models[i]) for i in range(num_clients)] # create a list of "clients"
    client_weights = [] # we will pull the weights from each client_model to average them
    for i, client in enumerate(clients):
        file_name = f'model_n{i}.pth'
        print(f'loading client model: {file_name}')
        client.load_model_dict(file_name)
        # evaluate the model
        print(f'evaluating client model {i}...')
        acc = client.evaluate()
        print(f'accuracy: {acc}')
        # append flattened parameters to the list
        client_weights.append(client.get_flattened_parameters())

    # # sanity check if the models are equal
    # print('sanity check: client weights...they should NOT be equal')
    # print(f'client weights equal: {compare_models(clients[0].model, clients[1].model)}')

    # # double check if client1 models is equal to server model
    # print('sanity check: client1 weights...they should NOT be equal')
    # print(f'client1 weights equal: {compare_models(clients[0].model, base_model)}')

    #average the weights
    print('averaging weights...')
    server = MnistServer(base_model) # create a server from the base model
    avg_weights = server.fedavg(client_weights)
    server_as_client.set_flattened_parameters(avg_weights) # set the weights of the server model to the average weights

    # evaluate the model
    print('evaluating model...')
    acc = server_as_client.evaluate()
    print(f'accuracy: {acc}')
    
    # save the model
    print('saving model...')
    server_as_client.save_model_dict('server_model.pth')

if __name__ == "__main__":
    main()




