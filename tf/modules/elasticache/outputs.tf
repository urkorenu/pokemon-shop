# Output the cache endpoint address of the first cache node in the cluster
output "cache_endpoint" {
  value = aws_elasticache_cluster.cluster.cache_nodes[0].address
}

# Output the name of the Elasticache subnet group
output "subnet_group_name" {
  value = aws_elasticache_subnet_group.subnet_group.name
}