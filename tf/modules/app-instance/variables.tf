# Variable for the name of the resource
variable "name" {}

# Variable for the instance type
variable "instance_type" {}

# Variable for the Amazon Machine Image (AMI) ID
variable "ami_id" {}

# Variable for the subnet ID
variable "subnet_id" {}

# Variable to associate a public IP address
variable "associate_public_ip" {}

# Variable for the security groups
variable "security_groups" {
  type = list(string)
}

# Variable for the key name
variable "key_name" {}

# Variable for the user data script path
variable "user_data" {
  description = "Path to the user data script"
  type        = string
  default     = "scripts/user_data.sh" # Path to the file
}

# Variable for the tags
variable "tags" {
  type = map(string)
}

# Variable for the on-demand base capacity
variable "on_demand_base_capacity" {
  default = 1
}

# Variable for the on-demand percentage above base capacity
variable "on_demand_percentage" {
  default = 0
}

# Variable for the spot allocation strategy
variable "spot_allocation_strategy" {
  default = "capacity-optimized"
}

# Variable for the minimum size of the Auto Scaling group
variable "min_size" {}

# Variable for the maximum size of the Auto Scaling group
variable "max_size" {}

# Variable for the desired capacity of the Auto Scaling group
variable "desired_capacity" {}

# Variable for the subnet IDs
variable "subnet_ids" {
  type = list(string)
}

# Variable for the target group ARNs
variable "target_group_arns" {
  type = list(string)
}

# Variable for the IAM role name
variable "iam_role_name" {}

# Variable for the IAM instance profile name
variable "iam_instance_profile_name" {}