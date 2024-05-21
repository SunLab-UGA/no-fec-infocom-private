# this is the main model which all server and client models inherit
# it can also be used as a standalone model for testing purposes


import torch
import numpy as np
from torchvision import datasets, transforms

class MnistModel(torch.nn.Module):
    def __init__(self):
        super(MnistModel, self).__init__()
        self.conv1 = torch.nn.Conv2d(1, 20, 5, 1)
        self.conv2 = torch.nn.Conv2d(20, 50, 5, 1)
        self.fc1 = torch.nn.Linear(4*4*50, 500)
        self.fc2 = torch.nn.Linear(500, 10)

    def forward(self, x):
        x = torch.nn.functional.relu(self.conv1(x))
        x = torch.nn.functional.max_pool2d(x, 2, 2)
        x = torch.nn.functional.relu(self.conv2(x))
        x = torch.nn.functional.max_pool2d(x, 2, 2)
        x = x.view(-1, 4*4*50)
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.fc2(x)
        return torch.nn.functional.log_softmax(x, dim=1)
    
# ============================================================================= load_data
def load_data(seed=0, batch_size=32, 
              data_dir='data',
              verbose=False):
    '''Load the MNIST dataset'''
    torch.manual_seed(seed)

    dataset_train = datasets.MNIST(data_dir, # directory to save the data
                         train=True, # train set, vs test set
                         download=True, # download if not found
                         transform=transforms.ToTensor() # convert directly to tensor
                         )

    trainset, valset = torch.utils.data.random_split(dataset_train, [50000, 10000]) # [train size, val size]
    dataset_test = datasets.MNIST(data_dir, train=False, download=True, transform=transforms.ToTensor())
    testset = torch.utils.data.Subset(dataset_test, range(1000)) # reduce the test set size

    
    # make the data loaders
    train_loader = torch.utils.data.DataLoader(trainset, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(valset, batch_size=batch_size, shuffle=True)
    test_loader = torch.utils.data.DataLoader(testset, batch_size=batch_size, shuffle=True)

    if verbose:
        print()
        print("Data loaded:")
        print(f'{len(trainset)=}')
        print(f'{len(valset)=}')
        print(f'{len(testset)=}')
        print()

    return train_loader, val_loader, test_loader
# ============================================================================= END load_data
# ============================================================================= train
def train(model, train_loader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    for i, data in enumerate(train_loader, 0):
        inputs, labels = data
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    return running_loss/len(train_loader)
# ============================================================================= END train
# ============================================================================= evaluate
def evaluate(model, test_loader, device):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data in test_loader:
            images, labels = data
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    return correct/total
# ============================================================================= END evaluate


# ============================================================================= MAIN
# run the main function to see the centralized example with some fixed hyperparameters
def main():
    VERBOSE = True

    if VERBOSE:
        print(f'** FL Client: MNIST Example **')
        print()
        print(f'{np.__version__=}')
        print(f'{torch.__version__=}')
        torch.manual_seed(42)
        rng_state = torch.random.get_rng_state()
        print(f'{rng_state=}')
        data_path = 'data'
        print(f'{data_path=}')
        # DEVICE: str = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        DEVICE = "cpu" # override, cuda does not work in this context
        print(f'{DEVICE=}')
        print()

    # model and dataloaders
    model = MnistModel()
    train_loader, val_loader, test_loader = load_data(seed=42, batch_size=32, verbose=VERBOSE)

    # hyperparameters
    batch_size = 32
    epochs = 5
    lr = 0.01
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)

    if VERBOSE:
        print(f'{batch_size=}')
        print(f'{epochs=}')
        print(f'learning_rate = {lr}')
        print()

    # train the model for a few epochs
    print(f'Training the model for {epochs} epochs...') if VERBOSE else None
    for epoch in range(epochs):
        running_loss = train(model, train_loader, optimizer, torch.nn.CrossEntropyLoss(), DEVICE)
        print(f"Epoch {epoch+1}/{epochs} - loss: {running_loss}") if VERBOSE else None

    # evaluate the model
    accuracy = evaluate(model, test_loader, DEVICE)
    print(f'Accuracy: {accuracy}')


if __name__ == "__main__":
    main() 
# ============================================================================= END MAIN

    