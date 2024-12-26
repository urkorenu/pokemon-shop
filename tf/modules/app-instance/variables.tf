variable "name" {}
variable "instance_type" {}
variable "ami_id" {}
variable "subnet_id" {}
variable "associate_public_ip" {}
variable "security_groups" { type = list(string) }
variable "key_name" {}
variable "user_data" {
  description = "Path to the user data script"
  type        = string
  default     = "scripts/user_data.sh" # Path to the file
}
variable "tags" { type = map(string) }
variable "on_demand_base_capacity" { default = 1 }
variable "on_demand_percentage" { default = 0 }
variable "spot_allocation_strategy" { default = "capacity-optimized" }
variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}
variable "subnet_ids" { type = list(string) }
variable "target_group_arns" { type = list(string) }
variable "iam_role_name" {}
variable "iam_instance_profile_name" {}
