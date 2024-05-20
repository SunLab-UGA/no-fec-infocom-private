#!/bin/bash

# This script sets up an NTP server and configures it to broadcast time to the local network.

# Obtain the primary IP address of the server (hope it's the primary one :/ )
MY_IP=$(hostname -I | cut -d' ' -f1) 

# Extract the first three octets and append .255 for the broadcast address
BROADCAST_ADDRESS=$(echo $MY_IP | cut -d'.' -f1-3).255

# Install NTP server
sudo apt-get update && sudo apt-get install -y ntp

# Configure NTP server
sudo cp /etc/ntp.conf /etc/ntp.conf.bak  # Backup the original config file

# Append local server configuration (adjust the network as needed)
# echo "restrict 192.168.1.0 mask 255.255.255.0 nomodify notrap" | sudo tee -a /etc/ntp.conf
echo "broadcast $MY_IP" | sudo tee -a /etc/ntp.conf  # Adjust broadcast address if necessary

# Restart NTP server to apply changes
sudo service ntp restart

echo "NTP server setup complete."
