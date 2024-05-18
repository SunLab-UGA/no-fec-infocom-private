#load a model and do some analysis

from fed_model.client import MnistClient
from fed_model.server import MnistServer, compare_models, compare_flattened_parameters
from fed_model.central_model import MnistModel

import numpy as np

# Load the model
model = MnistModel()
client = MnistClient(model)

# load the model from file
# file = "rx_client0_model_20240513-233325.pth"
file = "rx_client0_model_20240514-102350.pth"

client.load_model_dict(file)

# flatten the model parameters
flattened_params = client.get_flattened_parameters()
print("Flattened parameters: ", flattened_params)
print("Shape of the flattened parameters: ", flattened_params.shape)

# check if they are the same as a test (-1.1802468879641618e+29)
test_params = np.ones_like(flattened_params) * -1.1802468879641618e+29
# check if they are the same
same = compare_flattened_parameters(flattened_params, test_params)
print("Are the parameters the same? ", same)

# get the indexes of the parameters that are different
indexes = np.where(flattened_params != test_params)
print("Indexes of the different parameters: ", indexes)
print("Number of different parameters: ", len(indexes[0]))
print()

# get the parameters that are different
diff_params = flattened_params[indexes]
print("Different parameters: ", diff_params)