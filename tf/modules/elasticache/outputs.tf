output "cache_endpoint" {
  value = aws_elasticache_cluster.cluster.cache_nodes[0].address
}

output "subnet_group_name" {
  value = aws_elasticache_subnet_group.subnet_group.name
}
