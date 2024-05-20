#!/bin/bash

# IP of the NTP server
NTP_SERVER_IP="192.168.137.255"  # Change this to your server's IP address

# Install NTP
sudo apt-get update && sudo apt-get install -y ntp

# Configure NTP client
sudo cp /etc/ntp.conf /etc/ntp.conf.bak  # Backup the original config file

# Use server's IP as NTP server
echo "server $NTP_SERVER_IP" | sudo tee /etc/ntp.conf

# Restart NTP to apply changes
sudo service ntp restart

echo "NTP client setup complete. Syncing from $NTP_SERVER_IP."
echo "Waiting for 10 seconds before checking NTP status..."
sleep 10  # Wait for NTP sync
ntpq -p  # Display NTP peers and their status