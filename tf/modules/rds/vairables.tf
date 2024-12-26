variable "db_subnet_group_name" {
  description = "Name of the DB Subnet Group"
  type        = string
}

variable "db_subnet_group_description" {
  description = "Description of the DB Subnet Group"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the DB Subnet Group"
  type        = list(string)
}

variable "db_identifier" {
  description = "Identifier for the RDS instance"
  type        = string
}

variable "allocated_storage" {
  description = "Allocated storage for the RDS instance"
  type        = number
}

variable "storage_type" {
  description = "Storage type for the RDS instance"
  type        = string
}

variable "engine" {
  description = "Database engine"
  type        = string
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
}

variable "instance_class" {
  description = "Instance class for the RDS instance"
  type        = string
}

variable "username" {
  description = "Master username for the RDS instance"
  type        = string
}

variable "password" {
  description = "Master password for the RDS instance"
  type        = string
}

variable "db_name" {
  description = "Name of the database"
  type        = string
}

variable "publicly_accessible" {
  description = "Whether the RDS instance is publicly accessible"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "vpc_security_group_ids" {
  description = "List of VPC security group IDs for the RDS instance"
  type        = list(string)
}

variable "skip_final_snapshot" {
  description = "Whether to skip the final snapshot before deletion"
  type        = bool
  default     = true
}

variable "deletion_protection" {
  description = "Whether deletion protection is enabled"
  type        = bool
  default     = true
}

variable "snapshot_identifier" {
  description = "Snapshot identifier for the RDS instance"
  type        = string
  default     = null
}

variable "ignore_changes" {
  description = "List of attributes to ignore changes on"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
