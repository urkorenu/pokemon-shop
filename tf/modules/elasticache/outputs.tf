output "cache_endpoint" {
  value = "endpoint=${aws_elasticache_cluster.cluster.cache_nodes[0].address}:${aws_elasticache_cluster.cluster.cache_nodes[0].port}"
}

output "subnet_group_name" {
  value = aws_elasticache_subnet_group.subnet_group.name
}
