# Define a private subnet in the first availability zone
resource "aws_subnet" "private_zone1" {
  vpc_id            = aws_vpc.main.id  # VPC ID
  cidr_block        = "10.0.1.0/24"    # CIDR block for the subnet
  availability_zone = local.zone1      # Availability zone
  tags = { Name = "private-${local.zone1}" }  # Tags for the subnet
}

# Associate the private subnet in the first availability zone with the private route table
resource "aws_route_table_association" "private_zone1" {
  subnet_id      = aws_subnet.private_zone1.id  # Subnet ID
  route_table_id = aws_route_table.private.id   # Route table ID
}

# Define a private subnet in the second availability zone
resource "aws_subnet" "private_zone2" {
  vpc_id            = aws_vpc.main.id  # VPC ID
  cidr_block        = "10.0.2.0/24"    # CIDR block for the subnet
  availability_zone = local.zone2      # Availability zone
  tags = { Name = "private-${local.zone2}" }  # Tags for the subnet
}

# Associate the private subnet in the second availability zone with the private route table
resource "aws_route_table_association" "private_zone2" {
  subnet_id      = aws_subnet.private_zone2.id  # Subnet ID
  route_table_id = aws_route_table.private.id   # Route table ID
}

# Define a public subnet in the first availability zone
resource "aws_subnet" "public_zone1" {
  vpc_id                  = aws_vpc.main.id  # VPC ID
  cidr_block              = "10.0.3.0/24"    # CIDR block for the subnet
  availability_zone       = local.zone1      # Availability zone
  map_public_ip_on_launch = true             # Map public IP on launch
  tags = { Name = "public-${local.zone1}" }  # Tags for the subnet
}

# Associate the public subnet in the first availability zone with the public route table
resource "aws_route_table_association" "public_zone1" {
  subnet_id      = aws_subnet.public_zone1.id  # Subnet ID
  route_table_id = aws_route_table.public.id   # Route table ID
}

# Define a public subnet in the second availability zone
resource "aws_subnet" "public_zone2" {
  vpc_id            = aws_vpc.main.id  # VPC ID
  cidr_block        = "10.0.4.0/24"    # CIDR block for the subnet
  availability_zone = local.zone2      # Availability zone
  tags = { Name = "public-${local.zone2}" }  # Tags for the subnet
}

# Associate the public subnet in the second availability zone with the public route table
resource "aws_route_table_association" "public_zone2" {
  subnet_id      = aws_subnet.public_zone2.id  # Subnet ID
  route_table_id = aws_route_table.public.id   # Route table ID
}

# Define a private route table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id  # VPC ID
  route {
    cidr_block           = "0.0.0.0/0"  # Destination CIDR block
    network_interface_id = module.ec2_instance.nat_instance_network_interface_id  # Network interface ID for NAT instance
  }
  tags = { Name = "${local.env}-private" }  # Tags for the route table
}

# Define a public route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id  # VPC ID
  route {
    cidr_block = "0.0.0.0/0"  # Destination CIDR block
    gateway_id = aws_internet_gateway.igw.id  # Internet gateway ID
  }
  tags = { Name = "${local.env}-public" }  # Tags for the route table
}