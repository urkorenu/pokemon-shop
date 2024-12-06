#!/bin/bash

# Log the script output
exec > >(tee /var/log/user-data.log|logger -t user-data) 2>&1

# Update and install necessary tools
yum update -y
yum install -y git docker

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Install Docker Compose
DOCKER_COMPOSE_VERSION=2.22.0
curl -L "https://github.com/docker/compose/releases/download/v$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add ec2-user to the docker group
usermod -aG docker ec2-user

export DB_USERNAME=${DB_USERNAME}
export DB_PASSWORD=${DB_PASSWORD}
export DB_HOST=${DB_HOST}
export DB_NAME=${DB_NAME}
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export AWS_REGION=${AWS_REGION}
export S3_BUCKET=${S3_BUCKET}
export API_KEY=${API_KEY}

# Ensure the ec2-user owns the .env file
chown ec2-user:ec2-user /home/ec2-user/.env

# Mark setup as complete
touch /home/ec2-user/setup.log
chown ec2-user:ec2-user /home/ec2-user/setup.log
