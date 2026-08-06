variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "tfstate_bucket_name" {
  type    = string
  default = ""
}
variable "tfstate_lock_table" {
  type    = string
  default = ""
}
