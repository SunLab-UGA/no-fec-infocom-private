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
    #get the int time in milliseconds
    time_ms = int(time.time() * 1000)
    print("Time now (in ms):", time_ms)
    # add an offset to allow for loading the env starting the radio etc
    time_ms += 8_000 # ms
    print(f"Start on: +{time_ms}ms")

    username = 'sunlab'
    hostname1 = 'sunlab-832' # client0
    password = 'sunlab'
    conda_env = 'nofec'
    path = '~/no-fec-infocom-private/python/gnu_pmt/'
    python_filename = 'agent.py'
    t1 = threading.Thread(target=run_remote_script, 
                          args=(username, hostname1, password, conda_env, path, python_filename), 
                          kwargs={'whoami':'client0', 'action':'transmit', 'time':time_ms+50}) # +ms delay

    # 830 = server
    t2 = threading.Thread(target=run_local_script, 
                          args=(conda_env, path, python_filename), 
                          kwargs={'whoami':'server', 'action':'receive', 'time':time_ms,
                                  'from_who':'client0'})
    

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("All threads finished")
    

