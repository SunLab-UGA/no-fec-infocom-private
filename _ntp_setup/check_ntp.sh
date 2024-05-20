#!/bin/bash

# ssh and get the status of NTP, via ntpq -p
# this must be run on a machine that has sshpass installed (the server)

# Define the SSH user, hosts, and passwords, we use sshpass to avoid manual input of password
# Note: sshpass is not secure, it is better to use ssh keys for authentication
USER="sunlab"
HOST1="192.168.137.9" # 831
HOST2="192.168.137.204" # 832
PASSWORD1="sunlab"
PASSWORD2="sunlab"

# Command to get the NTP status
NTP_COMMAND="ntpq -p"

# Retrieve NTP status from both machines using sshpass
NTP_STATUS1=$(sshpass -p $PASSWORD1 ssh -o StrictHostKeyChecking=no $USER@$HOST1 $NTP_COMMAND)
echo "NTP status on $HOST1:"
echo "$NTP_STATUS1"

NTP_STATUS2=$(sshpass -p $PASSWORD2 ssh -o StrictHostKeyChecking=no $USER@$HOST2 $NTP_COMMAND)
echo "NTP status on $HOST2:"
echo "$NTP_STATUS2"

exit