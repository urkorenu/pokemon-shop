# Define an Internet Gateway (IGW) for the VPC
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  # Add tags to the Internet Gateway
  tags = {
    Name = "${local.env}"
  }
}