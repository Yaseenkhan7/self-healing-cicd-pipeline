data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}
resource "aws_iam_role" "ec2_role" {
  name               = "${var.ecr_repository_name}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}
resource "aws_iam_role_policy" "ec2_role_policy" {
  name   = "${var.ecr_repository_name}-ec2-policy"
  role   = aws_iam_role.ec2_role.id
  policy = file("${path.module}/iam/instance_policy.json")
}
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.ecr_repository_name}-instance-profile"
  role = aws_iam_role.ec2_role.name
}
data "aws_iam_policy_document" "github_oidc_assume" {
  statement {
    effect = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:<GITHUB_OWNER>/<REPO>:ref:refs/heads/*"]
    }
    principals {
      type        = "Federated"
      identifiers = ["arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"]
    }
  }
}
resource "aws_iam_role" "github_actions_role" {
  count              = var.create_github_oidc ? 1 : 0
  name               = "${var.ecr_repository_name}-github-actions-role"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_assume.json
}
resource "aws_iam_role_policy" "github_actions_policy_attach" {
  count  = var.create_github_oidc ? 1 : 0
  name   = "${var.ecr_repository_name}-github-actions-policy"
  role   = aws_iam_role.github_actions_role[0].id
  policy = file("${path.module}/iam/ci_policy.json")
}
