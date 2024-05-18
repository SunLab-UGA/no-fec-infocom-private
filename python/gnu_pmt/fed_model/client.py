# this is a client for the federated learning example using the MNIST dataset

# we load the model, dataloader, etc. from model.py

# we then train the model for a set number of epochs, evaluate the model on the test dataset, and save the weights to be sent back to the server

# here are the default args for the client:
# --batch_size 32 --epochs 1 --lr 0.01 --seed 42 --node_id 1
# the node_id is used to save the model to a file, so that we can differentiate between the clients
# the seed is used to set the random seed for the dataloaders (and should be DIFFERENT for each client)

from fed_model.central_model import MnistModel, load_data, train, evaluate
from fed_model.noise import add_noise_to_array

# use these imports to run as main
# from central_model import MnistModel, load_data, train, evaluate
# from noise import add_noise_to_array

import numpy as np
import torch

import argparse
import glob


class MnistClient():
    '''A simple client for federated learning using the MNIST dataset and Flower'''
    def __init__(self, 
                model: torch.nn.Module, 
                batch_size: int = 32, 
                epochs: int = 1, 
                lr: float = 0.01,
                seed: int = 42,
                device: str = "cpu" # default to cpu
        ) -> None:
        
        self.device = device
        self.model = model
        self.seed = seed

        # load the data
        self.trainloader, self.valloader, self.testloader = \
                    load_data(seed=seed, batch_size=batch_size, verbose=False)

        # set the hyperparameters
        self.batch_size = batch_size
        self.epochs = epochs
        self.lr = lr
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=self.lr)
        self.criterion = torch.nn.CrossEntropyLoss()

        # stats
        self.running_loss = float('inf') # set to infinity to start
        self.accuracy = 0
    
    # ======================================== Weight and Parameter Functions
    def get_parameters(self) -> list:
        ''''return the model parameters, as a list of numpy arrays'''
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]
    
    get_weights = get_parameters # alias get_weights to get_parameters

    def get_flattened_parameters(self) -> np.ndarray:
        '''return the model parameters as a single flattened numpy array'''
        return np.concatenate([val.cpu().numpy().flatten() for _, val in self.model.state_dict().items()])
    
    def set_flattened_parameters(self, flat_params: np.ndarray) -> None:
        '''set the model parameters from a single flattened numpy array'''
        start = 0
        for key, val in self.model.state_dict().items():
            end = start + val.numel()
            self.model.state_dict()[key].copy_(torch.Tensor(flat_params[start:end]).view_as(val))
            start = end
    
    def set_parameters(self, parameters: list) -> None:
        '''set the model parameters from a list of numpy arrays'''
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {key: torch.Tensor(val) for key, val in params_dict}
        self.model.load_state_dict(state_dict, strict=True)
    
    set_weights = set_parameters # alias set_weights to set_parameters

    def get_model_dict(self) -> dict:
        '''return the model dictionary'''
        return self.model.state_dict()

    def save_model_dict(self, path: str) -> None:
        '''save the model to a file'''
        torch.save(self.model.state_dict(), path)

    def load_model_dict(self, path: str) -> None:
        '''load the model from a file'''
        self.model.load_state_dict(torch.load(path))

    def print_model(self) -> None:
        '''print the model architecture'''
        print(self.model)

    def load_server_model(self) -> str:
        '''check for and load the most recently saved server model
        returns the filename of the loaded model
        if no model is found, a base model is loaded and None is returned'''
        try:
            # load the most recent model
            files = sorted(glob.glob('server_model_*.pth'))
            if files:
                latest_model = files[-1]
                print(f'loading model: {latest_model}')
                self.load_model_dict(latest_model)
                return latest_model
            else:
                print('no model found, base model will be used')
                return None
        except Exception as e:
            print(f'Error loading model: {e}')
            return None
    
    def load_server_model_with_noise(self, noise) -> str:
        '''check for and load the most recently saved server model
        returns the filename of the loaded model
        if no model is found, a base model is loaded and None is returned
        ADDITIONALLY, add noise to the weights of the model'''
        try:
            # load the most recent model
            files = sorted(glob.glob('server_model_*.pth'))
            if files:
                latest_model = files[-1]
                print(f'loading model: {latest_model}')
                self.load_model_dict(latest_model)
                clean_weights = self.get_flattened_parameters()
                # add noise to the weights
                noisey_weights = add_noise_to_array(self.get_flattened_parameters(), noise)
                self.set_flattened_parameters(noisey_weights)
                noisey_weights = self.get_flattened_parameters() # redundant, but for clarity
                if np.array_equal(clean_weights, noisey_weights): # sanity check
                    print('weights are equal! EXIT NOW!')
                    exit()

                return latest_model
            else:
                print('no model found, base model will be used')
                return None
        except Exception as e:
            print(f'Error loading model: {e}')
            return None


    # ======================================== Training and Evaluation Functions

    def fit(self, verbose=False) -> list:
        '''train the model on the client's dataset'''
        # trainloader = torch.utils.data.DataLoader(self.trainset, batch_size=self.batch_size, shuffle=True)
        self.running_loss = train(self.model, self.trainloader, self.optimizer, self.criterion, self.device)
        print(f"Loss: {self.running_loss}") if verbose else None
        return self.get_parameters()
    
    def evaluate(self) -> tuple[float,int,dict]:
        '''evaluate the model on the client's test dataset'''
        correct = 0
        total = 0
        with torch.no_grad():
            for data in self.testloader:
                images, labels = data
                images, labels = images.to(self.device), labels.to(self.device)
                outputs = self.model(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        self.accuracy = correct/total
        self.total = total
        # print(f'Accuracy: {accuracy}')
        # print(f'Total Tested: {total}')
        return float(self.accuracy), int(self.total)

# ============================================================================= MAIN
# lets run a client to train the model for a set number of epochs,
# then evaluate the model on the test dataset, and then "send" the weights back to the server   
def main():
    '''Load the model and data and start the client'''

    print(f'** FL Client: MNIST Example **')
    VERBOSE = True
    VERBOSE_WEIGHTS = False # print the weights to the console after training/evaluation

    # parse the command line arguments
    parser = argparse.ArgumentParser(description='Start a federated learning client')
    parser.add_argument('--batch_size', type=int, default=32, help='batch size for training')
    parser.add_argument('--epochs', type=int, default=1, help='number of epochs to train')
    parser.add_argument('--lr', type=float, default=0.001, help='learning rate') #0.01
    parser.add_argument('--seed', type=int, default=428, help='random seed') #42,428
    parser.add_argument('--node_id', type=int, default=1, choices=range(0,10), help='client node id') #0,1
    args = parser.parse_args()

    print(f'{args=}') if VERBOSE else None
    print() if VERBOSE else None # add a newline

    # load the data and model
    model = MnistModel()
    print(f'{model=}') if VERBOSE else None
    # DEVICE: str = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    DEVICE = "cpu" # override, cuda does not work in this context
    print(f'{DEVICE=}') if VERBOSE else None
    

    # create the client
    client = MnistClient(model, args.batch_size, args.epochs, args.lr, args.seed, DEVICE)

    # evaluate the model
    print("Evaluating the model before training")
    accuracy, total = client.evaluate()
    print(f'Accuracy: {accuracy}')
    print(f'Total Tested: {total}')
    print()
    
    # train the model
    print("Training the model...") if VERBOSE else None
    for epoch in range(args.epochs):
        weights = client.fit(verbose=VERBOSE) # train the model, get the weights, and print the loss if verbose
    print() if VERBOSE else None # add a newline

    # evaluate the model
    print("Evaluating the model...") if VERBOSE else None
    accuracy, total = client.evaluate()
    print(f'Accuracy: {accuracy}')
    print(f'Total Tested: {total}')

    # send the weights back to the server
    print(f'Sending weights back to the server...') if VERBOSE else None
    print(f'{len(weights)=}') if VERBOSE else None

    # get the shape of all the weights
    print("Weight shapes:") if VERBOSE else None
    for w in weights:
        print(w.shape) if VERBOSE else None
    print() if VERBOSE else None # add a newline
    # get the full length of all the weights combined
    total_weights = sum([w.size for w in weights])
    print(f'{total_weights=}') if VERBOSE else None

    # print the full model dictionary
    print("Model Dictionary:") if VERBOSE_WEIGHTS else None
    print(model.state_dict()) if VERBOSE_WEIGHTS else None

    # print(f'{weights=}') if VERBOSE_WEIGHTS else None # print only the weights

    # save the model to a file
    print("Saving the model to a file...") if VERBOSE else None
    client.save_model_dict(f'model_n{args.node_id}.pth')
    print(f'Model saved to model_n{args.node_id}.pth') if VERBOSE else None



if __name__ == "__main__":
    main()
# ============================================================================= END MAIN