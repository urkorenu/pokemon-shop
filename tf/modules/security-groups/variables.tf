# Variable for the VPC ID where the security groups will be created
variable "vpc_id" {
  description = "VPC ID where the security groups will be created"
  type        = string
}

# Variable for the environment name (e.g., dev, prod)
variable "env" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

# Variable for the IP address of the developer's machine for SSH access
variable "pc_ip" {
  description = "IP address of the developer's machine for SSH access"
  type        = string
}

# Variable for the private CIDR block for the VPC
variable "private_cidr_block" {
  description = "Private CIDR block for the VPC"
  type        = string
}

# Variable for the port for the application traffic
variable "app_port" {
  description = "Port for the application traffic"
  type        = number
  default     = 5000
}

# Variable for the tags to apply to all resources
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}