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

  name                   = "${local.env}-vpc"
  cidr_block             = "10.0.0.0/16"
  enable_dns_support     = true
  enable_dns_hostnames   = true
  nat_instance_network_interface_id = module.NAT_Bastion_Instance.network_interface_id

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

  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# Run the script to fetch the current IP address
resource "null_resource" "fetch_ip" {
  provisioner "local-exec" {
    command = "./scripts/fetch_ip.sh"
  }
}

# Load the IP address from the file
data "local_file" "ip" {
  filename = "scripts/ip.tfvars"
  depends_on = [null_resource.fetch_ip]
}

# Parse the IP address from the file
locals {
  pc_ip = regex("pc_ip = \"(.*)\"", data.local_file.ip.content)[0]
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security-groups"

  vpc_id            = module.vpc.vpc_id
  env               = local.env
  pc_ip             = local.pc_ip
  private_cidr_block = "10.0.0.0/16"
  app_port          = 5000

  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# NAT Bastion Instance Module
module "NAT_Bastion_Instance" {
  source          = "./modules/nat-instance"
  ami_id          = data.aws_ami.amazon_linux.id
  instance_type   = "t3.micro"
  key_name        = "pokemon-app"
  subnet_id       = module.vpc.public_subnet_ids[0]
  security_group  = module.security_groups.nat_bastion_sg_id
  instance_name   = "NAT-Bastion-Instance"
  vpc_id          = module.vpc.vpc_id
  private_route_table_id = module.vpc.private_route_table_id
}

# ELB Module
module "elb" {
  source = "./modules/elb"

  lb_name                  = "${local.env}-app-lb"
  internal                 = false
  security_groups          = [module.security_groups.elb_sg_id]
  subnets                  = module.vpc.public_subnet_ids
  idle_timeout             = 60
  acm_certificate_domain   = "pika-card.store"
  target_group_name        = "${local.env}-app-target-group"
  target_port              = 5000
  target_protocol          = "HTTP"
  vpc_id                   = module.vpc.vpc_id
  target_type              = "instance"
  health_check_enabled     = true
  health_check_path        = "/health"
  health_check_port        = "traffic-port"
  health_check_protocol    = "HTTP"
  health_check_matcher     = "200"
  health_check_interval    = 30
  health_check_timeout     = 5
  health_check_healthy_threshold = 3
  health_check_unhealthy_threshold = 2
  listener_port            = 443
  listener_protocol        = "HTTPS"
  ssl_policy               = "ELBSecurityPolicy-2016-08"

  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# Application Instance Module
module "app_instance" {
  source                   = "./modules/app-instance"
  name                     = "${local.env}-app"
  instance_type            = "t3.micro"
  ami_id                   = data.aws_ami.amazon_linux.id
  subnet_id                = module.vpc.private_subnet_ids[0]
  associate_public_ip      = false
  security_groups          = [module.security_groups.app_sg_id]
  key_name                 = "pokemon-app"
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
  tags                     = { Name = "${local.env}-app-instance" }
  on_demand_base_capacity  = 1
  min_size                 = 1
  max_size                 = 5
  desired_capacity         = 1
  subnet_ids               = module.vpc.private_subnet_ids
  target_group_arns        = [module.elb.target_group_arn]
  iam_role_name            = "app-role"
  iam_instance_profile_name = "app-instance-profile"
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  db_subnet_group_name        = "${local.env}-db-subnet-group"
  db_subnet_group_description = "DB Subnet Group for App"
  subnet_ids                  = module.vpc.private_subnet_ids
  db_identifier               = "${local.env}-db-instance"
  allocated_storage           = 20
  storage_type                = "gp2"
  engine                      = "postgres"
  engine_version              = "16.3"
  instance_class              = "db.t4g.micro"
  username                    = "admin"
  password                    = "guessit"
  db_name                     = "app_db"
  publicly_accessible         = false
  backup_retention_period     = 7
  vpc_security_group_ids      = [module.security_groups.rds_sg_id]
  skip_final_snapshot         = true
  deletion_protection         = true
  snapshot_identifier         = "init"
  ignore_changes              = ["username", "password"]

  tags = {
    Environment = local.env
    Critical    = "true"
  }
}

# Elasticache Module
module "elasticache" {
  source = "./modules/elasticache"

  subnet_group_name    = "${local.env}-cache-subnet-group"
  subnet_ids           = module.vpc.private_subnet_ids
  cluster_id           = "${local.env}-cache-cluster"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  security_group_ids   = [module.security_groups.cache_sg_id]

  tags = {
    Environment = local.env
    Project     = "Pokemon Shop"
  }
}

# Outputs
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "elb_dns_name" {
  value = module.elb.lb_dns_name
}

output "rds_endpoint" {
  value = module.rds.rds_endpoint
}

output "cache_endpoint" {
  value = module.elasticache.cache_endpoint
}


