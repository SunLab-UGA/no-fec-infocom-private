#!/bin/bash

# Define the SSH user, hosts, and passwords, we use sshpass to avoid manual input of password
# Note: sshpass is not secure, it is better to use ssh keys for authentication
USER="sunlab"
HOST1="192.168.137.9" # 831
HOST2="192.168.137.204" # 832
PASSWORD1="sunlab"
PASSWORD2="sunlab"

# Command to get the current time with milliseconds
TIME_COMMAND="date +%s%3N"  # %s%3N gives the epoch time in seconds and first three digits of nanoseconds which are milliseconds

# Retrieve time from both machines using sshpass
TIME1=$(sshpass -p $PASSWORD1 ssh -o StrictHostKeyChecking=no $USER@$HOST1 $TIME_COMMAND)
echo $TIME1
TIME2=$(sshpass -p $PASSWORD2 ssh -o StrictHostKeyChecking=no $USER@$HOST2 $TIME_COMMAND)
echo $TIME2
exit
# Calculate the difference
DIFF=$(echo "$TIME1 - $TIME2" | bc)

# Absolute value of difference
if [ $DIFF -lt 0 ]; then
  DIFF=$(echo "$DIFF * -1" | bc)
fi

# Output the times and the difference
echo "Time on $HOST1: $TIME1 ms"
echo "Time on $HOST2: $TIME2 ms"
echo "Difference: $DIFF ms"

# Optionally add a check to see if the difference is greater than a threshold
THRESHOLD=10  # Threshold in milliseconds
if [ $DIFF -gt $THRESHOLD ]; then
  echo "Warning: Time difference exceeds threshold."
else
  echo "Time synchronization within acceptable limits."
fi
