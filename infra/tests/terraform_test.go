package test
import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
)
func TestTerraformInfrastructure(t *testing.T) {
  t.Parallel()
  opts := &terraform.Options{
    TerraformDir: "../infra/terraform",
  }
  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)
  outputs := terraform.OutputAll(t, opts)
  assert.NotEmpty(t, outputs["ecr_repository_uri"])
  assert.NotEmpty(t, outputs["alb_dns_name"])
  assert.NotEmpty(t, outputs["scripts_bucket_name"])
}
