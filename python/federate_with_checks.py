# this script will run all the federated learning scripts in sequence with a timeout
# it will retry the script if it hangs and is terminated

# it will run the scripts X number of times

import subprocess
import time
import os
import glob
import re

# Number of Federated Learning rounds
federated_rounds = 10

# Maximum time allowed for each script to run (in seconds)
timeout_seconds = 30  # seconds

# Maximum retries if a script hangs and is terminated
max_retries = 3

# List of your scripts
scripts = ["app_train.py", "app_client0_to_server.py", "app_client1_to_server.py", "app_server_federate.py", "app_server_to_clients.py"]
python_path = "/home/sunlab/radioconda/envs/nofec/bin/python"

def run_script_with_timeout(script_path, timeout):
    #check if the script exists
    if not os.path.exists(script_path):
        print(f"Error: {script_path} is not found")
        return None

    attempts = 0
    while attempts < max_retries:
        try:
            print(f"Running {script_path}, attempt {attempts + 1}")
            # Run the script
            # result = subprocess.run(["python", script_path], timeout=timeout, check=True)
            result = subprocess.run([python_path, script_path], timeout=timeout, check=True, text=True, capture_output=True)
            print(f"Completed: {script_path}")
            return result
        except subprocess.TimeoutExpired:
            print(f"Timeout: {script_path} has not finished in {timeout} seconds, retrying...")
            attempts += 1
        except subprocess.CalledProcessError as e:
            # Handle cases where the script returns a non-zero exit code
            print(f"Error: {script_path} exited with status {e.returncode}")
            print(f"STDOUT: {e.stdout}")
            return None
    print(f"Failed: {script_path} exceeded the maximum retry limit")
    return None

if __name__ == "__main__":
    print("Starting Federated Learning")
    print()

    # Run each script in the list sequentially with a timeout
    for round in range(federated_rounds):
        print(f"Round {round + 1} of {federated_rounds}")

        for script in scripts:
            return_status = run_script_with_timeout(script, timeout_seconds)
            if return_status is None: # if the script failed
                print(f"Failed to run {script}")
                exit(1)
            
            # Get the most recent log file 
            log_files = glob.glob("~/no-fec-infocom-private/python/gnu_pmt/*.log")
            log_files.sort(key=os.path.getmtime)
            log_file = log_files[-1]

            # Check for federated accuracy if the script is the federate script
            if script == "app_server_federate.py":
                # open and parse for "fed accuracy:"
                with open(log_file, "r") as f:
                    for line in f:
                        if "fed accuracy:" in line:
                            print("FEDERATED ACCURACY:")
                            print(line)
                            break
            
            # check if the log indicates a known failure mode and exit
            with open(log_file, "r") as f:
                for line in f:
                    if "stderr:" in line:
                        print("ERROR FOUND IN LOG FILE!")
                        print(line)
                        print("Exiting...")
                        exit(1)

            # Sleep between scripts
            sleep_time = 10 # seconds
            print(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)

