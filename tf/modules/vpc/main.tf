# Main VPC
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_support   = var.enable_dns_support
  enable_dns_hostnames = var.enable_dns_hostnames

  tags = var.tags
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = var.tags
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(var.private_subnets)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnets[count.index].cidr_block
  availability_zone = var.private_subnets[count.index].availability_zone

  tags = merge(var.tags, { Name = var.private_subnets[count.index].name })
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = length(var.public_subnets)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnets[count.index].cidr_block
  availability_zone = var.public_subnets[count.index].availability_zone
  map_public_ip_on_launch = true

  tags = merge(var.tags, { Name = var.public_subnets[count.index].name })
}

# Route Tables
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = var.nat_instance_network_interface_id
  }

  tags = merge(var.tags, { Name = "${var.name}-private" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = merge(var.tags, { Name = "${var.name}-public" })
}

# Route Table Associations
resource "aws_route_table_association" "private" {
  count = length(var.private_subnets)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "public" {
  count = length(var.public_subnets)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

