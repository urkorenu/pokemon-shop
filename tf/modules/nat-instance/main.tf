variable "user_data" {
  description = "User data to be applied to the instance"
  type        = string
  default     = ""
}

resource "aws_instance" "ec2_instance" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group]

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

  tags = {
    Name = var.instance_name
  }
}


# Output for instance ID
output "ec2_instance_id" {
  value = aws_instance.ec2_instance.id
}

output "nat_instance_network_interface_id" {
  value = aws_instance.ec2_instance.primary_network_interface_id  # Correct attribute
}



