terraform {
  required_version = "= 1.16.6"
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "~> 3.2"
    }
  }
}
