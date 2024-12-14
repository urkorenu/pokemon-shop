# Define a module for an EC2 instance
module "ec2_instance" {
  source          = "./modules/nat-instance"  # Source path for the module
  ami_id          = "ami-0fcbdd3ee4f67a0a0"   # AMI ID for the instance
  instance_type   = "t3.micro"                # Instance type
  key_name        = "kafka"                   # Key pair name
  subnet_id       = aws_subnet.public_zone1.id # Subnet ID for the instance
  security_group  = aws_security_group.nat_bastion_sg.id # Security group ID
  instance_name   = "NAT-Bastion-Instance"    # Name of the instance
  vpc_id          = aws_vpc.main.id           # VPC ID
}

# Define a route for the NAT instance
resource "aws_route" "nat_route" {
  route_table_id         = aws_route_table.private.id # Route table ID
  destination_cidr_block = "0.0.0.0/0"                # Destination CIDR block
  network_interface_id   = module.ec2_instance.nat_instance_network_interface_id # Network interface ID

  lifecycle {
    create_before_destroy = false  # Do not create before destroying
    prevent_destroy       = false  # Do not prevent destroy
  }
  depends_on = [module.ec2_instance]  # Dependency on the EC2 instance module
}