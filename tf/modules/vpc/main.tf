# Main VPC
resource "aws_vpc" "main" {
  # CIDR block for the VPC
  cidr_block           = var.cidr_block
  # Enable DNS support in the VPC
  enable_dns_support   = var.enable_dns_support
  # Enable DNS hostnames in the VPC
  enable_dns_hostnames = var.enable_dns_hostnames

  # Tags to apply to the VPC
  tags = var.tags
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  # VPC ID to attach the Internet Gateway to
  vpc_id = aws_vpc.main.id

  # Tags to apply to the Internet Gateway
  tags = var.tags
}

# Private Subnets
resource "aws_subnet" "private" {
  # Number of private subnets to create
  count             = length(var.private_subnets)
  # VPC ID to attach the private subnets to
  vpc_id            = aws_vpc.main.id
  # CIDR block for each private subnet
  cidr_block        = var.private_subnets[count.index].cidr_block
  # Availability zone for each private subnet
  availability_zone = var.private_subnets[count.index].availability_zone

  # Tags to apply to each private subnet
  tags = merge(var.tags, { Name = var.private_subnets[count.index].name })
}

# Public Subnets
resource "aws_subnet" "public" {
  # Number of public subnets to create
  count             = length(var.public_subnets)
  # VPC ID to attach the public subnets to
  vpc_id            = aws_vpc.main.id
  # CIDR block for each public subnet
  cidr_block        = var.public_subnets[count.index].cidr_block
  # Availability zone for each public subnet
  availability_zone = var.public_subnets[count.index].availability_zone
  # Automatically assign public IP on launch
  map_public_ip_on_launch = true

  # Tags to apply to each public subnet
  tags = merge(var.tags, { Name = var.public_subnets[count.index].name })
}

# Route Tables
resource "aws_route_table" "private" {
  # VPC ID to attach the private route table to
  vpc_id = aws_vpc.main.id

  route {
    # CIDR block for the route
    cidr_block           = "0.0.0.0/0"
    # Network interface ID for the NAT instance
    network_interface_id = var.nat_instance_network_interface_id
  }

  # Tags to apply to the private route table
  tags = merge(var.tags, { Name = "${var.name}-private" })
}

resource "aws_route_table" "public" {
  # VPC ID to attach the public route table to
  vpc_id = aws_vpc.main.id

  route {
    # CIDR block for the route
    cidr_block = "0.0.0.0/0"
    # Internet Gateway ID for the route
    gateway_id = aws_internet_gateway.igw.id
  }

  # Tags to apply to the public route table
  tags = merge(var.tags, { Name = "${var.name}-public" })
}

# Route Table Associations
resource "aws_route_table_association" "private" {
  # Number of private subnets to associate
  count = length(var.private_subnets)
  # Subnet ID to associate with the private route table
  subnet_id      = aws_subnet.private[count.index].id
  # Route table ID to associate with the private subnet
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "public" {
  # Number of public subnets to associate
  count = length(var.public_subnets)
  # Subnet ID to associate with the public route table
  subnet_id      = aws_subnet.public[count.index].id
  # Route table ID to associate with the public subnet
  route_table_id = aws_route_table.public.id
}