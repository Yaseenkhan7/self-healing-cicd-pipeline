terraform {
  backend "s3" {
    bucket         = "<TFSTATE_BUCKET_NAME>"
    key            = "self-healing-cicd-pipeline/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "<TFSTATE_LOCK_TABLE>"
    encrypt        = true
  }
}
