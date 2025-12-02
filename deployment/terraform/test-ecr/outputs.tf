output "ecr_api_repository_url" {
  description = "URL of the API ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_nginx_repository_url" {
  description = "URL of the Nginx ECR repository"
  value       = aws_ecr_repository.nginx.repository_url
}

output "ecr_frontend_repository_url" {
  description = "URL of the Frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_api_repository_name" {
  description = "Name of the API ECR repository"
  value       = aws_ecr_repository.api.name
}

output "ecr_nginx_repository_name" {
  description = "Name of the Nginx ECR repository"
  value       = aws_ecr_repository.nginx.name
}

output "ecr_frontend_repository_name" {
  description = "Name of the Frontend ECR repository"
  value       = aws_ecr_repository.frontend.name
}

