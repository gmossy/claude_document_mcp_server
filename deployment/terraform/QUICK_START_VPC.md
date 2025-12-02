# Quick Start - Using Your Existing VPC

## Your VPC Information Summary

✅ **VPC ID**: `vpc-0f3105b0797e0c715`  
✅ **Region**: `us-gov-west-1`  
✅ **CIDR**: `172.31.0.0/16`  
✅ **Internet Gateway**: `igw-091694f31ae193e98`

## Your Subnets

All 3 subnets are **public subnets**:

| Subnet ID | AZ | CIDR | Use For |
|-----------|----|------|---------|
| `subnet-0c49610cf73743965` | us-gov-west-1a | 172.31.16.0/20 | ALB, ECS |
| `subnet-03bee96a64f553768` | us-gov-west-1b | 172.31.32.0/20 | ALB, ECS |
| `subnet-062946cb6065791e6` | us-gov-west-1c | 172.31.0.0/20 | ALB, ECS |

## terraform.tfvars Configuration

Copy this to your `terraform.tfvars` file:

```hcl
# AWS Configuration
aws_region   = "us-gov-west-1"
project_name = "document-gateway"
environment  = "prod"

# Use Existing VPC
use_existing_vpc = true
existing_vpc_id  = "vpc-0f3105b0797e0c715"

# Existing Public Subnets (for ALB)
existing_public_subnet_ids = [
  "subnet-0c49610cf73743965",  # us-gov-west-1a
  "subnet-03bee96a64f553768",  # us-gov-west-1b
  "subnet-062946cb6065791e6"   # us-gov-west-1c
]

# Existing Private Subnets (using public subnets since you don't have private ones)
# For better security, create private subnets later
existing_private_subnet_ids = [
  "subnet-0c49610cf73743965",  # us-gov-west-1a
  "subnet-03bee96a64f553768"   # us-gov-west-1b
]

# Internet Gateway (will auto-detect if not specified)
existing_internet_gateway_id = "igw-091694f31ae193e98"

# No NAT Gateway needed (all subnets are public)
enable_nat_gateway = false
enable_vpc_endpoints = true

# Rest of your configuration...
# (see terraform.tfvars.example for other settings)
```

## Important Notes

1. **All subnets are public**: Your ECS tasks will run in public subnets. This works but is less secure than private subnets.

2. **No NAT Gateway needed**: Since all subnets are public, set `enable_nat_gateway = false` to avoid unnecessary costs.

3. **Security Groups**: Terraform will create new security groups for ALB, ECS tasks, and RDS. These won't conflict with existing ones.

4. **Route Tables**: Your existing route table (`rtb-07f19176b56bcd0bb`) will be used. Terraform won't modify it.

## Next Steps

1. **Create terraform.tfvars**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit with your values above
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Review the plan**:
   ```bash
   terraform plan
   ```

4. **Apply** (when ready):
   ```bash
   terraform apply
   ```

## Optional: Create Private Subnets Later

For better security in production, consider creating private subnets:

1. Create 2-3 new subnets in your VPC (e.g., `172.31.48.0/20`, `172.31.64.0/20`)
2. Disable auto-assign public IP on these subnets
3. Create a NAT Gateway
4. Update `existing_private_subnet_ids` in terraform.tfvars
5. Re-run `terraform apply`

This is optional - the current setup will work fine with public subnets.

