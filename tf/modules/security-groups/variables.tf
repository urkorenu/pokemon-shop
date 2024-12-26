variable "vpc_id" {
  description = "VPC ID where the security groups will be created"
  type        = string
}

variable "env" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "pc_ip" {
  description = "IP address of the developer's machine for SSH access"
  type        = string
}

variable "private_cidr_block" {
  description = "Private CIDR block for the VPC"
  type        = string
}

variable "app_port" {
  description = "Port for the application traffic"
  type        = number
  default     = 5000
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
