# this is the main file that runs the full NOFEC-FEDERATED learing application
# load the environment variables

# server waits till two client models are received and saved
# then it averages the weights* saves the model and sends it back to the clients
# * always taking the newest model from the clients

# a client trains a model, saves, and waits to transmit
# on a sync time it transmits the model to the server
# then it waits for a new saved model from the server
# (if none it resends the same model at the next sync time)

import subprocess

def run_remote_script(username, hostname, password, conda_env, remote_script_path,  **kwargs):
    # Convert args tuple to a space-separated string for the command line
    kwargs_string = ' '.join(f"--{key} {value}" for key, value in kwargs.items())
    full_command_string = f"{kwargs_string}".strip()
    print("Full Command String:", full_command_string)
    
    # Command to activate conda environment and run the Python script
    command = (
        f"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{hostname} "
        f"\"source ~/radioconda/etc/profile.d/conda.sh && conda activate {conda_env} && python {remote_script_path} {full_command_string}\""
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

if __name__ == "__main__":

    username = 'sunlab'
    hostname1 = 'sunlab-831'
    password = 'sunlab'
    conda_env = 'nofec'
    remote_script_path = '~/no-fec-infocom-private/python/gnu_pmt/agent.py'

    run_remote_script(username=username, hostname=hostname1, password=password,
                      conda_env=conda_env, remote_script_path=remote_script_path,
                      whoami='client1', action='train')
    

