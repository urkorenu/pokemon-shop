variable "name" {
  description = "Name of the VPC"
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "enable_dns_support" {
  description = "Enable DNS support in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "private_subnets" {
  description = "Configuration for private subnets"
  type = list(object({
    cidr_block        = string
    availability_zone = string
    name              = string
  }))
}

variable "public_subnets" {
  description = "Configuration for public subnets"
  type = list(object({
    cidr_block        = string
    availability_zone = string
    name              = string
  }))
}

variable "nat_instance_network_interface_id" {
  description = "Network Interface ID of the NAT instance"
  type        = string
}

variable "tags" {
  description = "Tags to be applied to all resources"
  type        = map(string)
  default     = {}
}
