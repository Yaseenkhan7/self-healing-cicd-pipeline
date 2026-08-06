output "ecr_repository_uri" {
  value = aws_ecr_repository.app.repository_url
}
output "alb_dns_name" {
  value = aws_lb.alb.dns_name
}
output "scripts_bucket_name" {
  value = aws_s3_bucket.scripts.bucket
}
