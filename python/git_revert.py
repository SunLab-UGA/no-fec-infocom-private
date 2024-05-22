# uses git revert on both clients
# dont use this...just use git ignore on the logs and models

import subprocess
import threading

def run_remote_script(username, hostname, password, conda_env, 
                      path, python_filename,  **kwargs):
    # Convert args tuple to a space-separated string for the command line
    kwargs_string = ' '.join(f"--{key} {value}" for key, value in kwargs.items())
    full_command_string = f"{kwargs_string}".strip()
    # print("Command kwargs:", full_command_string)
    print(f"HARD RESET ON CLIENTS")
    input("Press Enter to continue...")

    command = (
    f"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{hostname} "
    f"&& cd {path} "
    f"&& git reset --hard origin/main"
    f"\""
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
    #831 = client1
    username = 'sunlab'
    hostname1 = 'sunlab-831'
    password = 'sunlab'
    conda_env = 'nofec'
    path = '~/no-fec-infocom-private/'
    python_filename = 'agent.py'
    t1 = threading.Thread(target=run_remote_script, 
                          args=(username, hostname1, password, conda_env, path, python_filename), 
                          kwargs={'whoami':'client1', 'action':'train'})
    # run_remote_script(username=username, hostname=hostname1, password=password, conda_env=conda_env,
    #                   path=path, python_filename=python_filename,
    #                   whoami='client1', action='train')
    #832 = client0
    username = 'sunlab'
    hostname1 = 'sunlab-832'
    password = 'sunlab'
    conda_env = 'nofec'
    path = '~/no-fec-infocom-private/'
    python_filename = 'agent.py'
    t2 = threading.Thread(target=run_remote_script, 
                          args=(username, hostname1, password, conda_env, path, python_filename), 
                          kwargs={'whoami':'client0', 'action':'train'})
    
    # run_remote_script(username=username, hostname=hostname1, password=password, conda_env=conda_env,
    #                   path=path, python_filename=python_filename,
    #                   whoami='client0', action='train')

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("GIT IS RESET ON CLIENTS")
    

