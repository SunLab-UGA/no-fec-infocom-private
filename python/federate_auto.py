# this script will run federate_with_checks_logging.py
# it will then collect and clear the logs and then proceed based on the exit status of the script
# exit status 0: (the script ran successfully!) and end
# exit status 1: (the script failed, but keep the logs) and retry
# exit status 2: (the script failed, and might have lingering processes) and retry

# run until exit status 0 is reached or the run limit is reached

# WIP!


import subprocess
import time
import os
import glob
import logging

# run limit
run_limit = 100 # don't run more than 100 times
timeout_minutes = 15
DEBUG_SLOW_MODE = True # gives time after each run error for user action

collect_script = os.path.expanduser("~/no-fec-infocom-private/collect_data.sh") # clear option to collect and clear logs
clear_script = os.path.expanduser("~/no-fec-infocom-private/clear_data.sh")
close_script = os.path.expanduser("~/no-fec-infocom-private/close_ports.sh") # used to close any lingering processes with open ports (if needed)

python_path = "/home/sunlab/radioconda/envs/nofec/bin/python"
python_script = os.path.expanduser("~/no-fec-infocom-private/python/federate_with_checks_logging.py")

print(f"collect_script: {collect_script}")
print(f"clear_script: {clear_script}")
print(f"close_script: {close_script}")
print(f"python_script: {python_script}")

def run_script_with_timeout(script_path, timeout_minutes):
        '''Run a python script with a timeout in minutes'''
        #check if the script exists
        if not os.path.exists(script_path):
            print(f"Error: {script_path} is not found")
            return None
        
        timeout = timeout_minutes * 60 # convert minutes to seconds

        try:
            # result = subprocess.run(['python', script_path], text=True, capture_output=True)
            result = subprocess.run([python_path, script_path], timeout=timeout, check=True, text=True, capture_output=True)
            logging.info(f"Completed: {script_path}")
            return result.returncode
        except subprocess.TimeoutExpired:
            logging.info(f"Timeout: {script_path} has not finished in {timeout_minutes} minutes")
            logging.info(f"Exiting...")
            return None
        except subprocess.CalledProcessError as e:
            # Handle cases where the script returns a non-zero exit code
            logging.info(f"Error: {script_path} exited with status {e.returncode}")
            logging.info(f"STDOUT: {e.stdout}")
            return e.returncode

def run_shell_script_with_timeout(script_path:str, timeout_minutes=0.25, clear=False): 
        '''Run a shell script with a timeout in minutes, clear is used to add the clear argument to the script collect_data.sh'''
        #check if the script exists
        if not os.path.exists(script_path):
            print(f"Error: {script_path} is not found")
            return None
        
        timeout = timeout_minutes * 60 # convert minutes to seconds

        try:
            result = subprocess.run([script_path], timeout=timeout, check=True, text=True, capture_output=True)
            logging.info(f"Completed: {script_path}")
            return result.returncode
        except subprocess.TimeoutExpired:
            logging.info(f"Timeout: {script_path} has not finished in {timeout_minutes} minutes")
            logging.info(f"Exiting...")
            return None
        except subprocess.CalledProcessError as e:
            # Handle cases where the script returns a non-zero exit code
            logging.info(f"Error: {script_path} exited with status {e.returncode}")
            logging.info(f"STDOUT: {e.stdout}")
            return e.returncode

# ===================================================================================================== MAIN LOOP
# Set up logging
time_suffix = time.strftime("%Y%m%d-%H%M%S")
logging.basicConfig(filename=f'auto_federated_log{time_suffix}.auto_log', # auto_log prevents collection of the log file
                filemode= 'w',
                format='%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level=logging.INFO)
# setup a console logger (to print logging to console)
console = logging.StreamHandler()
console.setLevel(logging.INFO) # debug, info, warning, error, critical 
logging.getLogger('').addHandler(console)

logging.info("Starting Federated Learning AUTO")

for round in range(run_limit): # run until a full run is completed successfully or the run limit is reached
    print("")
    print("=====================================================================")
    print(time.strftime("%Y-%m-%d %H:%M:%S")) # print the time, no need to log

    logging.info(f"=== Trial {round} ===")
    logging.info(f"Running {python_script}...")
    result = run_script_with_timeout(python_script, timeout_minutes=timeout_minutes)

    # based on the exit code we exit or retry
    if result == 0: # success
        logging.info("Trial Completed")
        logging.info("Collecting logs...")
        cmd = f"{collect_script} clear" # collect and clear the logs
        sh_result = subprocess.run([cmd], shell=True, check=True, text=True, capture_output=True)
        logging.info(f"{cmd}, exit status {sh_result.returncode}")
        break # exit

    elif result == 1: # failed (extra handling required, keep logs and retry)
        logging.info("Trial Failed")
        logging.info("Process may still be running")
        # run close_script bash script which handles any process with open ports
        try:
            cmd = f"{close_script} 50011" # 50011 is the port number that gets stuck open if a script reports an error
            result = subprocess.run([cmd], shell=True, check=True, text=True, capture_output=True) 
            logging.info(f"{cmd}, exit status {result.returncode}")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                logging.info(f"Error: {close_script} exited with status {e.returncode}")
                exit(1)
            if e.returncode == 2: # no port/pid was found open (no action needed)
                logging.info(f"Error: {close_script} exited with status {e.returncode}")

        logging.info("keeping logs")
        cmd = f"{collect_script} clear" # collect and clear the logs
        sh_result = subprocess.run([cmd], shell=True, check=True, text=True, capture_output=True)
        logging.info(f"{cmd}, exit status {sh_result.returncode}")
        logging.info("Waiting 10 Seconds...") if DEBUG_SLOW_MODE else None; time.sleep(10) if DEBUG_SLOW_MODE else None

    elif result >= 2: # failed ( 2 + itterations completed), do log management and retry
        logging.info("Trial Failed")
        if result >= 4: # keep the logs
            logging.info("keeping logs")
            cmd = f"{collect_script} clear" # collect and clear the logs
            sh_result = subprocess.run([cmd], shell=True, check=True, text=True, capture_output=True)
            logging.info(f"{cmd}, exit status {sh_result.returncode}")
            logging.info("Waiting 10 Seconds...") if DEBUG_SLOW_MODE else None; time.sleep(10) if DEBUG_SLOW_MODE else None
        else: # clear the logs
            logging.info("clearing logs")
            cmd = f"{collect_script} clear" # collect and clear the logs
            sh_result = subprocess.run([cmd], shell=True, check=True, text=True, capture_output=True)
            logging.info(f"{cmd}, exit status {sh_result.returncode}")
            logging.info("Waiting 10 Seconds...") if DEBUG_SLOW_MODE else None; time.sleep(10) if DEBUG_SLOW_MODE else None
            
    else:
        logging.info("Unknown Error")
        break
    
    
logging.info("Trials Finished")
