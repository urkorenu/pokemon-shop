# Define an Elasticache Subnet Group
resource "aws_elasticache_subnet_group" "subnet_group" {
  # Name of the subnet group
  name       = var.subnet_group_name
  # List of subnet IDs for the subnet group
  subnet_ids = var.subnet_ids

  # Tags to assign to the subnet group
  tags = merge(var.tags, { Name = var.subnet_group_name })
}

# Define an Elasticache Cluster
resource "aws_elasticache_cluster" "cluster" {
  # ID of the cluster
  cluster_id           = var.cluster_id
  # Engine type for the cluster (e.g., redis, memcached)
  engine               = var.engine
  # Node type for the cluster
  node_type            = var.node_type
  # Number of cache nodes in the cluster
  num_cache_nodes      = var.num_cache_nodes
  # Name of the parameter group to associate with the cluster
  parameter_group_name = var.parameter_group_name
  # Name of the subnet group to associate with the cluster
  subnet_group_name    = aws_elasticache_subnet_group.subnet_group.name
  # List of security group IDs to associate with the cluster
  security_group_ids   = var.security_group_ids

  # Tags to assign to the cluster
  tags = merge(var.tags, { Name = var.cluster_id })
}