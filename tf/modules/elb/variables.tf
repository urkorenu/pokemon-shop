variable "lb_name" {
  description = "Name of the Load Balancer"
  type        = string
}

variable "internal" {
  description = "Whether the Load Balancer is internal"
  type        = bool
  default     = false
}

variable "security_groups" {
  description = "Security groups for the Load Balancer"
  type        = list(string)
}

variable "subnets" {
  description = "Subnets for the Load Balancer"
  type        = list(string)
}

variable "idle_timeout" {
  description = "Idle timeout for the Load Balancer"
  type        = number
  default     = 60
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "acm_certificate_domain" {
  description = "Domain name for the ACM certificate"
  type        = string
}

variable "target_group_name" {
  description = "Name of the Target Group"
  type        = string
}

variable "target_port" {
  description = "Port for the Target Group"
  type        = number
}

variable "target_protocol" {
  description = "Protocol for the Target Group"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for the Target Group"
  type        = string
}

variable "target_type" {
  description = "Target type (e.g., instance, ip, lambda)"
  type        = string
  default     = "instance"
}

variable "health_check_enabled" {
  description = "Enable health checks"
  type        = bool
  default     = true
}

variable "health_check_path" {
  description = "Path for the health check"
  type        = string
}

variable "health_check_port" {
  description = "Port for the health check"
  type        = string
}

variable "health_check_protocol" {
  description = "Protocol for the health check"
  type        = string
}

variable "health_check_matcher" {
  description = "Health check matcher (e.g., 200)"
  type        = string
}

variable "health_check_interval" {
  description = "Interval between health checks"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Timeout for health checks"
  type        = number
  default     = 5
}

variable "health_check_healthy_threshold" {
  description = "Healthy threshold for health checks"
  type        = number
  default     = 3
}

variable "health_check_unhealthy_threshold" {
  description = "Unhealthy threshold for health checks"
  type        = number
  default     = 2
}

variable "listener_port" {
  description = "Port for the Listener"
  type        = number
  default     = 443
}

variable "listener_protocol" {
  description = "Protocol for the Listener"
  type        = string
  default     = "HTTPS"
}

variable "ssl_policy" {
  description = "SSL policy for the Listener"
  type        = string
  default     = "ELBSecurityPolicy-2016-08"
}
