# Variable for the AMI ID for the EC2 instance
variable "ami_id" {
  description = "The AMI ID for the EC2 instance"
  type        = string
}

# Variable for the EC2 instance type (e.g., t2.micro)
variable "instance_type" {
  description = "The EC2 instance type (e.g., t2.micro)"
  type        = string
}

# Variable for the key pair name to allow SSH access
variable "key_name" {
  description = "Key pair name to allow SSH access"
  type        = string
  default     = "eli-nat"
}

# Variable for the subnet ID where the EC2 instance will be created
variable "subnet_id" {
  description = "The subnet ID where the EC2 instance will be created"
  type        = string
}

# Variable for the name tag for the EC2 instance
variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
  default     = "MyEC2Instance"
}

# Variable for the security group ID for the NAT instance
variable "security_group" {
  description = "Security group ID for the NAT instance"
  type        = string
}

# Variable for the VPC ID where the security group is created
variable "vpc_id" {
  description = "The VPC ID where the security group is created"
  type        = string
}

# Variable for the route table ID for the private subnet
variable "private_route_table_id" {
  description = "The route table ID for the private subnet"
  type        = string
}