data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}
resource "aws_launch_template" "app_lt" {
  name_prefix   = "${var.ecr_repository_name}-lt-"
  image_id      = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }
  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.instance_sg.id]
  }
  user_data = base64encode(templatefile("${path.module}/userdata.tpl", {
    scripts_bucket = aws_s3_bucket.scripts.bucket,
    region         = var.aws_region
  }))
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.ecr_repository_name}-instance"
    }
  }
}
resource "aws_lb" "alb" {
  name               = "${var.ecr_repository_name}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = [for s in aws_subnet.public : s.id]
  security_groups    = [aws_security_group.alb_sg.id]
}
resource "aws_lb_target_group" "app" {
  name     = "${var.ecr_repository_name}-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  health_check {
    path                = "/health"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }
}
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
resource "aws_autoscaling_group" "app_asg" {
  name                      = "${var.ecr_repository_name}-asg"
  max_size                  = var.asg_max
  min_size                  = var.asg_min
  desired_capacity          = var.asg_desired
  launch_template {
    id      = aws_launch_template.app_lt.id
    version = "$Latest"
  }
  vpc_zone_identifier = [for s in aws_subnet.public : s.id]
  target_group_arns   = [aws_lb_target_group.app.arn]
  tag {
    key                 = "Name"
    value               = "${var.ecr_repository_name}-asg"
    propagate_at_launch = true
  }
  health_check_type = "ELB"
  force_delete      = true
}
output "alb_dns_name" {
  value = aws_lb.alb.dns_name
}
output "ecr_repository_uri" {
  value = aws_ecr_repository.app.repository_url
}
