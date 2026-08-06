resource "random_id" "scripts" {
  byte_length = 4
}
resource "aws_s3_bucket" "scripts" {
  bucket = "${var.ecr_repository_name}-scripts-${random_id.scripts.hex}"
  acl    = "private"
  versioning {
    enabled = true
  }
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}
resource "aws_s3_bucket_public_access_block" "scripts_block" {
  bucket = aws_s3_bucket.scripts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
output "scripts_bucket_name" {
  value = aws_s3_bucket.scripts.bucket
}
