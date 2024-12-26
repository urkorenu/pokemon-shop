# Elasticache Subnet Group
resource "aws_elasticache_subnet_group" "subnet_group" {
  name       = var.subnet_group_name
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, { Name = var.subnet_group_name })
}

# Elasticache Cluster
resource "aws_elasticache_cluster" "cluster" {
  cluster_id           = var.cluster_id
  engine               = var.engine
  node_type            = var.node_type
  num_cache_nodes      = var.num_cache_nodes
  parameter_group_name = var.parameter_group_name
  subnet_group_name    = aws_elasticache_subnet_group.subnet_group.name
  security_group_ids   = var.security_group_ids

  tags = merge(var.tags, { Name = var.cluster_id })
}
