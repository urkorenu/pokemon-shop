terraform {
  backend "s3" {
    bucket         = "pokemon-production-tf-state"       # Name of the S3 bucket
    key            = "terraform/state.tfstate"   # Path to the state file
    region         = "eu-north-1"                # AWS region
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = local.region
}
