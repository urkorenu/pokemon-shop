terraform {
  backend "s3" {
    bucket         = "pokemon-production-tf-state"
    key            = "terraform/state.tfstate"
    region         = "eu-north-1"
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
