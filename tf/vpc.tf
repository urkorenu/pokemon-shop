# Define the main VPC for the application
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"  # CIDR block for the VPC
  enable_dns_support   = true           # Enable DNS support
  enable_dns_hostnames = true           # Enable DNS hostnames

  tags = {
    Name = "${local.env}-main"  # Tags for the VPC
  }
}