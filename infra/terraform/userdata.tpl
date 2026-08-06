#!/bin/bash
set -e
yum update -y
amazon-linux-extras install docker -y || true
service docker start || true
usermod -a -G docker ec2-user || true
yum install -y jq || true
if ! systemctl is-active --quiet amazon-ssm-agent; then
  yum install -y amazon-ssm-agent || true
  systemctl enable amazon-ssm-agent || true
  systemctl start amazon-ssm-agent || true
fi
aws s3 cp s3://${scripts_bucket}/deploy_on_instance.sh /tmp/deploy_on_instance.sh || true
chmod +x /tmp/deploy_on_instance.sh || true
/tmp/deploy_on_instance.sh || true
