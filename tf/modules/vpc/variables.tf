# Variable for the name of the VPC
variable "name" {
  description = "Name of the VPC"
  type        = string
}

# Variable for the CIDR block for the VPC
variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
}

# Variable to enable DNS support in the VPC
variable "enable_dns_support" {
  description = "Enable DNS support in the VPC"
  type        = bool
  default     = true
}

# Variable to enable DNS hostnames in the VPC
variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

# Variable for the configuration of private subnets
variable "private_subnets" {
  description = "Configuration for private subnets"
  type = list(object({
    cidr_block        = string
    availability_zone = string
    name              = string
  }))
}

# Variable for the configuration of public subnets
variable "public_subnets" {
  description = "Configuration for public subnets"
  type = list(object({
    cidr_block        = string
    availability_zone = string
    name              = string
  }))
}

# Variable for the network interface ID of the NAT instance
variable "nat_instance_network_interface_id" {
  description = "Network Interface ID of the NAT instance"
  type        = string
}

# Variable for the tags to be applied to all resources
variable "tags" {
  description = "Tags to be applied to all resources"
  type        = map(string)
  default     = {}
}