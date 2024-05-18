# this is the main file that runs the full NOFEC-FEDERATED learing application
# load the environment variables

# server waits till two client models are received and saved
# then it averages the weights* saves the model and sends it back to the clients
# * always taking the newest model from the clients

# a client trains a model, saves, and waits to transmit
# on a sync time it transmits the model to the server
# then it waits for a new saved model from the server
# (if none it resends the same model at the next sync time)

