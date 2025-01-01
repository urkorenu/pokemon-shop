# Variable for the name of the DB Subnet Group
variable "db_subnet_group_name" {
  description = "Name of the DB Subnet Group"
  type        = string
}

# Variable for the description of the DB Subnet Group
variable "db_subnet_group_description" {
  description = "Description of the DB Subnet Group"
  type        = string
}

# Variable for the list of subnet IDs for the DB Subnet Group
variable "subnet_ids" {
  description = "List of subnet IDs for the DB Subnet Group"
  type        = list(string)
}

# Variable for the identifier of the RDS instance
variable "db_identifier" {
  description = "Identifier for the RDS instance"
  type        = string
}

# Variable for the allocated storage (in GB) for the RDS instance
variable "allocated_storage" {
  description = "Allocated storage for the RDS instance"
  type        = number
}

# Variable for the storage type of the RDS instance (e.g., standard, gp2, io1)
variable "storage_type" {
  description = "Storage type for the RDS instance"
  type        = string
}

# Variable for the database engine (e.g., MySQL, PostgreSQL)
variable "engine" {
  description = "Database engine"
  type        = string
}

# Variable for the version of the database engine
variable "engine_version" {
  description = "Database engine version"
  type        = string
}

# Variable for the instance class of the RDS instance (e.g., db.t2.micro)
variable "instance_class" {
  description = "Instance class for the RDS instance"
  type        = string
}

# Variable for the master username of the RDS instance
variable "username" {
  description = "Master username for the RDS instance"
  type        = string
}

# Variable for the master password of the RDS instance
variable "password" {
  description = "Master password for the RDS instance"
  type        = string
}

# Variable for the name of the database
variable "db_name" {
  description = "Name of the database"
  type        = string
}

# Variable to specify if the RDS instance is publicly accessible
variable "publicly_accessible" {
  description = "Whether the RDS instance is publicly accessible"
  type        = bool
  default     = false
}

# Variable for the backup retention period (in days)
variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

# Variable for the list of VPC security group IDs for the RDS instance
variable "vpc_security_group_ids" {
  description = "List of VPC security group IDs for the RDS instance"
  type        = list(string)
}

# Variable to specify if the final snapshot should be skipped before deletion
variable "skip_final_snapshot" {
  description = "Whether to skip the final snapshot before deletion"
  type        = bool
  default     = true
}

# Variable to specify if deletion protection is enabled
variable "deletion_protection" {
  description = "Whether deletion protection is enabled"
  type        = bool
  default     = true
}

# Variable for the snapshot identifier to restore the RDS instance from
variable "snapshot_identifier" {
  description = "Snapshot identifier for the RDS instance"
  type        = string
  default     = null
}

# Variable for the list of attributes to ignore changes on
variable "ignore_changes" {
  description = "List of attributes to ignore changes on"
  type        = list(string)
  default     = []
}

# Variable for the tags to apply to all resources
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}