#!/bin/bash

# comes from this manual function
# port suck open?
# lsof -i :50011
# kill -9 [PID given above]

# UNTESTED!!!


# Check if a port number is provided
if [ -z "$1" ]
then
  echo "Usage: $0 <port>"
  exit 1
fi

PORT=$1

# Find processes associated with the specified port
PIDS=$(lsof -t -i :$PORT)

# Check if any PIDs were found
if [ -z "$PIDS" ]
then
  echo "No process found on port $PORT."
  exit 2
fi

echo "Killing processes on port $PORT with PIDs: $PIDS"
# Kill processes
for PID in $PIDS
do
  kill -9 $PID
done

echo "Processes killed."
