# Output the ID of the VPC
output "vpc_id" {
  value = aws_vpc.main.id
}

# Output the IDs of the private subnets
output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

# Output the IDs of the public subnets
output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

# Output the ID of the Internet Gateway
output "igw_id" {
  value = aws_internet_gateway.igw.id
}

# Output the ID of the private route table
output "private_route_table_id" {
  value = aws_route_table.private.id
}

# Output the ID of the public route table
output "public_route_table_id" {
  value = aws_route_table.public.id
}