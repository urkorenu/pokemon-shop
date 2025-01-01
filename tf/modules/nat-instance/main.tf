# Variable for user data to be applied to the instance
variable "user_data" {
  description = "User data to be applied to the instance"
  type        = string
  default     = ""
}

# Resource for the NAT instance
resource "aws_instance" "nat_instance" {
  # AMI ID for the instance
  ami                    = var.ami_id
  # Instance type
  instance_type          = var.instance_type
  # Key name for SSH access
  key_name               = var.key_name
  # Subnet ID for the instance
  subnet_id              = var.subnet_id
  # Security group IDs for the instance
  vpc_security_group_ids = [var.security_group]

  # Disable source/destination checks for NAT functionality
  source_dest_check = false

  # NAT instance user data script
  user_data = <<-EOF
    #!/bin/bash
    # Enable IP forwarding for NAT functionality
    sudo yum install iptables-services -y
    sudo systemctl enable iptables
    sudo systemctl start iptables

    echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/custom-ip-forwarding.conf > /dev/null
    sudo sysctl -p /etc/sysctl.d/custom-ip-forwarding.conf

    iface=$(netstat -i | awk 'NR>2 {print $1}' | grep -E '^(eth|en)' | head -n 1)

    sudo /sbin/iptables -t nat -A POSTROUTING -o $iface -j MASQUERADE
    sudo /sbin/iptables -F FORWARD
    sudo service iptables save

    # Enable SSH for Bastion functionality
    sudo yum update -y
    sudo yum install -y openssh-server
    sudo systemctl enable sshd
    sudo systemctl start sshd
  EOF

  # Tags for the instance
  tags = {
    Name = var.instance_name
  }
}

# Fetch the existing route table
data "aws_route_table" "private_route_table" {
  route_table_id = var.private_route_table_id
}

# Check if a route for 0.0.0.0/0 already exists
locals {
  route_exists = length([
    for route in data.aws_route_table.private_route_table.routes : route
    if route.cidr_block == "0.0.0.0/0"
  ]) > 0
}

# Define a route for the NAT instance only if it doesn't already exist
resource "aws_route" "nat_route" {
  count                = local.route_exists ? 0 : 1
  route_table_id       = var.private_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id = aws_instance.nat_instance.primary_network_interface_id

  lifecycle {
    ignore_changes = [destination_cidr_block]
    create_before_destroy = true
    prevent_destroy       = false
  }

  depends_on = [aws_instance.nat_instance]
}

# Output for instance ID
output "ec2_instance_id" {
  value = aws_instance.nat_instance.id
}

# Output for NAT instance network interface ID
output "nat_instance_network_interface_id" {
  value = aws_instance.nat_instance.primary_network_interface_id
}