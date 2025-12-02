# VPC and Networking Information Checklist for AWS GovCloud

Use this checklist to gather all required networking information from your AWS GovCloud account.

## ✅ Information You've Provided
- **VPC ID**: `vpc-0f3105b0797e0c715`
- **Region**: `us-gov-west-1` (US-Gov-West)
- **VPC CIDR**: `172.31.0.0/16`

## 📋 Required Information to Gather

### 1. VPC Details
- [x] VPC ID: `vpc-0f3105b0797e0c715`
- [x] VPC CIDR Block: `172.31.0.0/16`
- [ ] VPC Name/Tags (optional, for reference)
- [ ] DNS Hostnames Enabled: `true` or `false`
- [ ] DNS Support Enabled: `true` or `false`

**AWS CLI Command:**
```bash
aws ec2 describe-vpcs --vpc-ids vpc-0f3105b0797e0c715 --region us-gov-west-1
```

### 2. Subnets

#### Public Subnets (for ALB and NAT Gateway)
You need at least 2 public subnets in different availability zones.

For each public subnet, collect:
- [ ] **Subnet ID** (e.g., `subnet-xxxxx`)
- [ ] **CIDR Block** (e.g., `172.31.1.0/24`)
- [ ] **Availability Zone** (e.g., `us-gov-west-1a`)
- [ ] **Route Table ID** (for verification)

**AWS CLI Command:**
```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1 --query 'Subnets[?MapPublicIpOnLaunch==`true`]'
```

#### Private Subnets (for ECS Tasks)
You need at least 2 private subnets in different availability zones.

For each private subnet, collect:
- [ ] **Subnet ID** (e.g., `subnet-xxxxx`)
- [ ] **CIDR Block** (e.g., `172.31.10.0/24`)
- [ ] **Availability Zone** (e.g., `us-gov-west-1b`)
- [ ] **Route Table ID** (for verification)

**AWS CLI Command:**
```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1 --query 'Subnets[?MapPublicIpOnLaunch==`false`]'
```

#### Database Subnets (for RDS, if using)
- [ ] **Subnet ID 1** (e.g., `subnet-xxxxx`)
- [ ] **Subnet ID 2** (e.g., `subnet-xxxxx`)
- [ ] **CIDR Blocks** for each
- [ ] **Availability Zones** for each

**AWS CLI Command:**
```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1
```

### 3. Internet Gateway
- [ ] **Internet Gateway ID** (e.g., `igw-xxxxx`)
- [ ] Verify it's attached to your VPC

**AWS CLI Command:**
```bash
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1
```

### 4. NAT Gateway (if exists)
If you already have a NAT Gateway, collect:
- [ ] **NAT Gateway ID** (e.g., `nat-xxxxx`)
- [ ] **Elastic IP Address** (e.g., `x.x.x.x`)
- [ ] **Subnet ID** where it's located
- [ ] **Availability Zone**

**AWS CLI Command:**
```bash
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1
```

### 5. Route Tables
- [ ] **Public Route Table ID** (for public subnets)
- [ ] **Private Route Table ID** (for private subnets, if separate)
- [ ] Verify routes (0.0.0.0/0 -> IGW for public, -> NAT for private)

**AWS CLI Command:**
```bash
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1
```

### 6. Security Groups
Check if you want to use existing security groups or create new ones:
- [ ] **ALB Security Group ID** (if exists, or we'll create new)
- [ ] **ECS Tasks Security Group ID** (if exists, or we'll create new)
- [ ] **RDS Security Group ID** (if exists, or we'll create new)

**AWS CLI Command:**
```bash
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1
```

### 7. VPC Endpoints (Optional but Recommended)
Check if you have existing VPC endpoints:
- [ ] **ECR API Endpoint** (if exists)
- [ ] **ECR DKR Endpoint** (if exists)
- [ ] **S3 Endpoint** (if exists)
- [ ] **CloudWatch Logs Endpoint** (if exists)

**AWS CLI Command:**
```bash
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=vpc-0f3105b0797e0c715" --region us-gov-west-1
```

### 8. Availability Zones
- [ ] List of available AZs in your region (e.g., `us-gov-west-1a`, `us-gov-west-1b`, `us-gov-west-1c`)

**AWS CLI Command:**
```bash
aws ec2 describe-availability-zones --region us-gov-west-1
```

## 📝 Quick Data Collection Script

Save this as `collect-vpc-info.sh` and run it:

```bash
#!/bin/bash
VPC_ID="vpc-0f3105b0797e0c715"
REGION="us-gov-west-1"

echo "=== VPC Information ==="
aws ec2 describe-vpcs --vpc-ids $VPC_ID --region $REGION --query 'Vpcs[0]' --output json

echo -e "\n=== Subnets ==="
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --region $REGION --output table

echo -e "\n=== Internet Gateway ==="
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --region $REGION --output table

echo -e "\n=== NAT Gateways ==="
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --region $REGION --output table

echo -e "\n=== Route Tables ==="
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --region $REGION --output table

echo -e "\n=== Security Groups ==="
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --region $REGION --query 'SecurityGroups[*].[GroupId,GroupName,Description]' --output table

echo -e "\n=== VPC Endpoints ==="
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --region $REGION --output table

echo -e "\n=== Availability Zones ==="
aws ec2 describe-availability-zones --region $REGION --query 'AvailabilityZones[*].[ZoneName,State]' --output table
```

## 🎯 Minimum Required Information

**Minimum to proceed:**
1. ✅ VPC ID: `vpc-0f3105b0797e0c715`
2. ✅ VPC CIDR: `172.31.0.0/16`
3. [ ] At least 2 Public Subnet IDs
4. [ ] At least 2 Private Subnet IDs
5. [ ] Internet Gateway ID (or we'll create one if missing)

**Recommended:**
- NAT Gateway ID (or we'll create one)
- Route Table IDs (for verification)
- Security Group IDs (or we'll create new ones)

## 📌 Notes

- If subnets don't exist, we can create them in the Terraform script
- If NAT Gateway doesn't exist, we can create one (costs apply)
- Security groups will be created new to avoid conflicts
- VPC endpoints are optional but recommended for cost savings

