# this holds functions which are subprocesses which are run on the server.
# they can call a script on the server or on the client
# the server then threads these functions to run them in parallel

import subprocess
import threading
import time

def run_remote_script(username, hostname, password, conda_env, 
                      path, python_filename,  **kwargs):
    # Convert args tuple to a space-separated string for the command line
    kwargs_string = ' '.join(f"--{key} {value}" for key, value in kwargs.items())
    full_command_string = f"{kwargs_string}".strip()
    print("Command kwargs:", full_command_string)

    command = (
    f"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{hostname} "
    f"\"source ~/radioconda/etc/profile.d/conda.sh && conda activate {conda_env} "
    f"&& date +%s%3N "
    f"&& cd {path} && python {python_filename} {full_command_string}\""
    f"&& date +%s%3N"
    )
    
    # Execute the command
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except subprocess.CalledProcessError as e:
        print("Error occurred:", e)
        print("Return Code:", e.returncode)
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)

def run_local_script(conda_env, path, python_filename, **kwargs):
    # Convert args tuple to a space-separated string for the command line
    kwargs_string = ' '.join(f"--{key} {value}" for key, value in kwargs.items())
    full_command_string = f"{kwargs_string}".strip()
    print("Command kwargs:", full_command_string)

    command = (
        f"bash -c 'source ~/radioconda/etc/profile.d/conda.sh && "
        f"conda activate {conda_env} && "
        f"date +%s%3N && "
        f"cd {path} && "
        f"python {python_filename} {full_command_string} && "
        f"date +%s%3N'"
    )
    
    # Execute the command
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except subprocess.CalledProcessError as e:
        print("Error occurred:", e)
        print("Return Code:", e.returncode)
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
