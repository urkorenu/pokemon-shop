#!/bin/bash
# Update and install required packages
yum update -y
yum install -y docker git
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Start Docker service
systemctl start docker
systemctl enable docker

# Set environment variables
cat <<EOF > /etc/environment
DB_USERNAME=${DB_USERNAME}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_REGION=${AWS_REGION}
S3_BUCKET=${S3_BUCKET}
API_KEY=${API_KEY}
ADMIN_MAIL=${ADMIN_MAIL}
ELASTIC_CACHE=${ELASTIC_CACHE}
EOF

# Load environment variables
export $(cat /etc/environment | xargs)

# Create application directory and fetch Docker Compose configuration
cd /home/ec2-user/
git clone -b main https://github.com/urkorenu/pokemon-shop.git && cd pokemon-shop

# Pull latest Docker image and run application
docker-compose pull
docker-compose --env-file /etc/environment up -d

# Verify the application is running
docker ps --filter name=app --format '{{.Status}}'

