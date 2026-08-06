terraform {
  backend "s3" {
    bucket         = "<PUT_YOUR_BUCKET_NAME>"
    key            = "self-healing-cicd-pipeline/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "<PUT_YOUR_LOCK_TABLE>"
    encrypt        = true
  }
}
