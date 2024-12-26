resource "aws_elasticache_subnet_group" "pokemon_cache_subnet_group" {
  name       = "pokemon-app-cache-subnet-group"
  subnet_ids = [aws_subnet.private_zone1.id, aws_subnet.private_zone2.id]

  tags = {
    Name = "pokemon-app-cache-subnet-group"
  }
}

resource "aws_elasticache_cluster" "pokemon_cache" {
  cluster_id           = "pokemon-app-cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.pokemon_cache_subnet_group.name
  security_group_ids   = [aws_security_group.cache_sg.id]  # Attach Security Group

  tags = {
    Name = "pokemon-app-cache"
  }
}


output "cache_endpoint" {
  value = "endpoint=${aws_elasticache_cluster.pokemon_cache.cache_nodes.0.address}:${aws_elasticache_cluster.pokemon_cache.cache_nodes.0.port}"
}