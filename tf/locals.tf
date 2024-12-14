# Define local variables for the Terraform configuration
locals {
  # Environment name
  env              = "production"

  # AWS region
  region           = "eu-north-1"

  # Availability Zone 1
  zone1            = "eu-north-1a"

  # Availability Zone 2
  zone2            = "eu-north-1b"
}