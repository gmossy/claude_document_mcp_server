# ============================================================================
# AMAZON BEDROCK CONFIGURATION
# ============================================================================
# Configures access to Bedrock LLM services for document processing.

# ============================================================================
# BEDROCK MODEL ACCESS
# ============================================================================
# Note: Bedrock model access must be granted through the AWS Console
# or CLI. This resource documents the configuration but access is
# typically managed through the Bedrock console.
#
# To enable Bedrock access:
# 1. Go to AWS Bedrock Console
# 2. Navigate to Model access
# 3. Request access to the desired model (e.g., Claude)
# 4. Wait for approval
#
# The IAM policy for Bedrock is configured in iam.tf

# ============================================================================
# IAM POLICY FOR BEDROCK ACCESS
# ============================================================================
# The IAM policy for Bedrock access is already defined in iam.tf
# This file serves as documentation and can be extended with:
# - Bedrock model fine-tuning configurations
# - Bedrock knowledge base configurations
# - Custom model endpoints

# ============================================================================
# OUTPUTS (documentation)
# ============================================================================
# Bedrock configuration outputs are in outputs.tf

