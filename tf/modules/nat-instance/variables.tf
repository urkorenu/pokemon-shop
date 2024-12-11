variable "ami_id" {
  description = "The AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "The EC2 instance type (e.g., t2.micro)"
  type        = string
}

variable "key_name" {
  description = "Key pair name to allow SSH access"
  type        = string
  default     = "eli-nat"
}

variable "subnet_id" {
  description = "The subnet ID where the EC2 instance will be created"
  type        = string
}

variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
  default     = "MyEC2Instance"
}

variable "security_group" {
  description = "Security group ID for the NAT instance"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID where the security group is created"
  type        = string
}