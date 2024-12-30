# Data source to fetch the most recent Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"] # Amazon Linux 2
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  # Name of the VPC
  name                   = "${local.env}-vpc"
  # CIDR block for the VPC
  cidr_block             = "10.0.0.0/16"
  # Enable DNS support in the VPC
  enable_dns_support     = true
  # Enable DNS hostnames in the VPC
  enable_dns_hostnames   = true
  # Network interface ID for the NAT instance
  nat_instance_network_interface_id = module.NAT_Bastion_Instance.network_interface_id

  # Configuration for private subnets
  private_subnets = [
    {
      cidr_block        = "10.0.1.0/24"
      availability_zone = local.zone1
      name              = "private-${local.zone1}"
    },
    {
      cidr_block        = "10.0.2.0/24"
      availability_zone = local.zone2
      name              = "private-${local.zone2}"
    }
  ]

  # Configuration for public subnets
  public_subnets = [
    {
      cidr_block        = "10.0.3.0/24"
      availability_zone = local.zone1
      name              = "public-${local.zone1}"
    },
    {
      cidr_block        = "10.0.4.0/24"
      availability_zone = local.zone2
      name              = "public-${local.zone2}"
    }
  ]

  # Tags to apply to the VPC
  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# Resource to run the script to fetch the current IP address
resource "null_resource" "fetch_ip" {
  provisioner "local-exec" {
    command = "./scripts/fetch_ip.sh"
  }
}

# Data source to load the IP address from the file
data "local_file" "ip" {
  filename = "scripts/ip.tfvars"
  depends_on = [null_resource.fetch_ip]
}

# Local value to parse the IP address from the file
locals {
  pc_ip = regex("pc_ip = \"(.*)\"", data.local_file.ip.content)[0]
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security-groups"

  # VPC ID
  vpc_id            = module.vpc.vpc_id
  # Environment name
  env               = local.env
  # IP address of the developer's machine
  pc_ip             = local.pc_ip
  # Private CIDR block for the VPC
  private_cidr_block = "10.0.0.0/16"
  # Port for the application traffic
  app_port          = 5000

  # Tags to apply to the security groups
  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# NAT Bastion Instance Module
module "NAT_Bastion_Instance" {
  source          = "./modules/nat-instance"
  # AMI ID for the instance
  ami_id          = data.aws_ami.amazon_linux.id
  # Instance type
  instance_type   = "t3.micro"
  # Key name for SSH access
  key_name        = "pokemon-app"
  # Subnet ID for the instance
  subnet_id       = module.vpc.public_subnet_ids[0]
  # Security group for the instance
  security_group  = module.security_groups.nat_bastion_sg_id
  # Name of the instance
  instance_name   = "NAT-Bastion-Instance"
  # VPC ID
  vpc_id          = module.vpc.vpc_id
  # Private route table ID
  private_route_table_id = module.vpc.private_route_table_id
}

# ELB Module
module "elb" {
  source = "./modules/elb"

  # Load balancer name
  lb_name                  = "${local.env}-app-lb"
  # Internal load balancer
  internal                 = false
  # Security groups for the load balancer
  security_groups          = [module.security_groups.elb_sg_id]
  # Subnets for the load balancer
  subnets                  = module.vpc.public_subnet_ids
  # Idle timeout for the load balancer
  idle_timeout             = 60
  # ACM certificate domain
  acm_certificate_domain   = "pika-card.store"
  # Target group name
  target_group_name        = "${local.env}-app-target-group"
  # Target port
  target_port              = 5000
  # Target protocol
  target_protocol          = "HTTP"
  # VPC ID
  vpc_id                   = module.vpc.vpc_id
  # Target type
  target_type              = "instance"
  # Health check enabled
  health_check_enabled     = true
  # Health check path
  health_check_path        = "/health"
  # Health check port
  health_check_port        = "traffic-port"
  # Health check protocol
  health_check_protocol    = "HTTP"
  # Health check matcher
  health_check_matcher     = "200"
  # Health check interval
  health_check_interval    = 30
  # Health check timeout
  health_check_timeout     = 5
  # Healthy threshold for health checks
  health_check_healthy_threshold = 3
  # Unhealthy threshold for health checks
  health_check_unhealthy_threshold = 2
  # Listener port
  listener_port            = 443
  # Listener protocol
  listener_protocol        = "HTTPS"
  # SSL policy
  ssl_policy               = "ELBSecurityPolicy-2016-08"

  # Tags to apply to the load balancer
  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# Application Instance Module
module "app_instance" {
  source                   = "./modules/app-instance"
  # Name of the instance
  name                     = "${local.env}-app"
  # Instance type
  instance_type            = "t3.micro"
  # AMI ID for the instance
  ami_id                   = data.aws_ami.amazon_linux.id
  # Subnet ID for the instance
  subnet_id                = module.vpc.private_subnet_ids[0]
  # Associate public IP
  associate_public_ip      = false
  # Security groups for the instance
  security_groups          = [module.security_groups.app_sg_id]
  # Key name for SSH access
  key_name                 = "pokemon-app"
  # User data script for the instance
  user_data = base64encode(templatefile("${path.module}/templates/user_data.tpl", {
    DB_USERNAME         = module.rds.db_username,
    DB_PASSWORD         = module.rds.db_password,
    DB_HOST             = module.rds.rds_endpoint,
    DB_NAME             = module.rds.db_name,
    AWS_ACCESS_KEY_ID   = local.aws_access_key_id,
    AWS_SECRET_ACCESS_KEY = local.aws_secret_access_key,
    AWS_REGION          = local.aws_region,
    S3_BUCKET           = data.aws_s3_bucket.pokemon_pics.id,
    API_KEY             = local.api_key,
    ADMIN_MAIL          = local.admin_mail,
    ELASTIC_CACHE       = module.elasticache.cache_endpoint,
  }))
  # Tags to apply to the instance
  tags                     = { Name = "${local.env}-app-instance" }
  # On-demand base capacity
  on_demand_base_capacity  = 1
  # Minimum size of the auto-scaling group
  min_size                 = 1
  # Maximum size of the auto-scaling group
  max_size                 = 5
  # Desired capacity of the auto-scaling group
  desired_capacity         = 1
  # Subnet IDs for the auto-scaling group
  subnet_ids               = module.vpc.private_subnet_ids
  # Target group ARNs for the auto-scaling group
  target_group_arns        = [module.elb.target_group_arn]
  # IAM role name for the instance
  iam_role_name            = "app-role"
  # IAM instance profile name for the instance
  iam_instance_profile_name = "app-instance-profile"
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  # DB subnet group name
  db_subnet_group_name        = "${local.env}-db-subnet-group"
  # Description for the DB subnet group
  db_subnet_group_description = "DB Subnet Group for App"
  # Subnet IDs for the DB subnet group
  subnet_ids                  = module.vpc.private_subnet_ids
  # DB instance identifier
  db_identifier               = "${local.env}-db-instance"
  # Allocated storage for the DB instance
  allocated_storage           = 20
  # Storage type for the DB instance
  storage_type                = "gp2"
  # Database engine
  engine                      = "postgres"
  # Engine version
  engine_version              = "16.3"
  # Instance class for the DB instance
  instance_class              = "db.t4g.micro"
  # Username for the DB instance
  username                    = "admin"
  # Password for the DB instance
  password                    = "guessit"
  # Database name
  db_name                     = "app_db"
  # Publicly accessible
  publicly_accessible         = false
  # Backup retention period
  backup_retention_period     = 7
  # VPC security group IDs for the DB instance
  vpc_security_group_ids      = [module.security_groups.rds_sg_id]
  # Skip final snapshot on deletion
  skip_final_snapshot         = true
  # Enable deletion protection
  deletion_protection         = true
  # Snapshot identifier for the DB instance
  snapshot_identifier         = "init"
  # Ignore changes to specific attributes
  ignore_changes              = ["username", "password"]

  # Tags to apply to the DB instance
  tags = {
    Environment = local.env
    Critical    = "true"
  }
}

# Elasticache Module
module "elasticache" {
  source = "./modules/elasticache"

  # Subnet group name for the cache cluster
  subnet_group_name    = "${local.env}-cache-subnet-group"
  # Subnet IDs for the cache cluster
  subnet_ids           = module.vpc.private_subnet_ids
  # Cache cluster ID
  cluster_id           = "${local.env}-cache-cluster"
  # Cache engine
  engine               = "redis"
  # Node type for the cache cluster
  node_type            = "cache.t3.micro"
  # Number of cache nodes
  num_cache_nodes      = 1
  # Parameter group name for the cache cluster
  parameter_group_name = "default.redis7"
  # Security group IDs for the cache cluster
  security_group_ids   = [module.security_groups.cache_sg_id]

  # Tags to apply to the cache cluster
  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# Output the ID of the VPC
output "vpc_id" {
  value = module.vpc.vpc_id
}

# Output the DNS name of the ELB
output "elb_dns_name" {
  value = module.elb.lb_dns_name
}

# Output the endpoint of the RDS instance
output "rds_endpoint" {
  value = module.rds.rds_endpoint
}

# Output the endpoint of the Elasticache cluster
output "cache_endpoint" {
  value = module.elasticache.cache_endpoint
}