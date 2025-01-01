# Variable for the name of the Elasticache Subnet Group
variable "subnet_group_name" {
  description = "Name of the Elasticache Subnet Group"
  type        = string
}

# Variable for the list of subnet IDs for the Elasticache Subnet Group
variable "subnet_ids" {
  description = "List of subnet IDs for the Elasticache Subnet Group"
  type        = list(string)
}

# Variable for the identifier of the Elasticache cluster
variable "cluster_id" {
  description = "Identifier for the Elasticache cluster"
  type        = string
}

# Variable for the cache engine type for Elasticache
variable "engine" {
  description = "Cache engine for Elasticache"
  type        = string
  default     = "redis"
}

# Variable for the node type of the Elasticache cluster
variable "node_type" {
  description = "Node type for the Elasticache cluster"
  type        = string
}

# Variable for the number of cache nodes in the Elasticache cluster
variable "num_cache_nodes" {
  description = "Number of cache nodes in the Elasticache cluster"
  type        = number
  default     = 1
}

# Variable for the name of the parameter group for the Elasticache cluster
variable "parameter_group_name" {
  description = "Name of the parameter group for the Elasticache cluster"
  type        = string
  default     = "default.redis7"
}

# Variable for the list of security group IDs for the Elasticache cluster
variable "security_group_ids" {
  description = "List of security group IDs for the Elasticache cluster"
  type        = list(string)
}

# Variable for the tags to apply to all resources
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}