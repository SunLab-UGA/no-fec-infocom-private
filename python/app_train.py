# this is the main file that runs the full NOFEC-FEDERATED learing application
# load the environment variables

# server waits till two client models are received and saved
# then it averages the weights* saves the model and sends it back to the clients
# * always taking the newest model from the clients

# a client trains a model, saves, and waits to transmit
# on a sync time it transmits the model to the server
# then it waits for a new saved model from the server
# (if none it resends the same model at the next sync time)

from run import run_remote_script, run_local_script
import threading
import time

if __name__ == "__main__":
    #831 = client1
    username = 'sunlab'
    hostname1 = 'sunlab-831'
    password = 'sunlab'
    conda_env = 'nofec'
    path = '~/no-fec-infocom-private/python/gnu_pmt/'
    python_filename = 'agent.py'
    t1 = threading.Thread(target=run_remote_script, 
                          args=(username, hostname1, password, conda_env, path, python_filename), 
                          kwargs={'whoami':'client1', 'action':'train', 'seed':42})

    #832 = client0
    username = 'sunlab'
    hostname1 = 'sunlab-832'
    password = 'sunlab'
    conda_env = 'nofec'
    path = '~/no-fec-infocom-private/python/gnu_pmt/'
    python_filename = 'agent.py'
    t2 = threading.Thread(target=run_remote_script, 
                          args=(username, hostname1, password, conda_env, path, python_filename), 
                          kwargs={'whoami':'client0', 'action':'train', 'seed':0})
    

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("All threads finished")
    

