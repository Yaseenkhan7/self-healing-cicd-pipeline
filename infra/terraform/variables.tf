variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "aws_account_id" {
  type    = string
  default = ""
}
variable "ecr_repository_name" {
  type    = string
  default = "self-healing-demo"
}
variable "instance_type" {
  type    = string
  default = "t3.small"
}
variable "asg_min" {
  type    = number
  default = 1
}
variable "asg_desired" {
  type    = number
  default = 2
}
variable "asg_max" {
  type    = number
  default = 3
}
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}
variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}
variable "ecr_force_delete" {
  type    = bool
  default = false
}
