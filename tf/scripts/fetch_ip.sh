#!/bin/bash

# Fetch the public IP address of your PC
PC_IP=$(curl -s http://checkip.amazonaws.com)

# Save the IP address to a file
echo "pc_ip = \"${PC_IP}\"" > ip.tfvars