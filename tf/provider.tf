# Configure the Terraform backend to use an S3 bucket for storing the state file
terraform {
  backend "s3" {
    bucket         = "pokemon-production-tf-state"  # S3 bucket name
    key            = "terraform/state.tfstate"      # Path to the state file within the bucket
    region         = "eu-north-1"                   # AWS region of the S3 bucket
    encrypt        = true                           # Enable encryption for the state file
  }

  # Specify the required providers and their versions
  required_providers {
    aws = {
      source  = "hashicorp/aws"  # Source of the AWS provider
      version = "~> 4.0"         # Version constraint for the AWS provider
    }
  }
}

# Configure the AWS provider
provider "aws" {
  region = local.region  # AWS region to use, defined in local variables
}