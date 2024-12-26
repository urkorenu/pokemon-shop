variable "subnet_group_name" {
  description = "Name of the Elasticache Subnet Group"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the Elasticache Subnet Group"
  type        = list(string)
}

variable "cluster_id" {
  description = "Identifier for the Elasticache cluster"
  type        = string
}

variable "engine" {
  description = "Cache engine for Elasticache"
  type        = string
  default     = "redis"
}

variable "node_type" {
  description = "Node type for the Elasticache cluster"
  type        = string
}

variable "num_cache_nodes" {
  description = "Number of cache nodes in the Elasticache cluster"
  type        = number
  default     = 1
}

variable "parameter_group_name" {
  description = "Name of the parameter group for the Elasticache cluster"
  type        = string
  default     = "default.redis7"
}

variable "security_group_ids" {
  description = "List of security group IDs for the Elasticache cluster"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
