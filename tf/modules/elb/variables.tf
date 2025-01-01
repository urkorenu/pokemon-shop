# Variable for the name of the Load Balancer
variable "lb_name" {
  description = "Name of the Load Balancer"
  type        = string
}

# Variable to specify if the Load Balancer is internal
variable "internal" {
  description = "Whether the Load Balancer is internal"
  type        = bool
  default     = false
}

# Variable for the security groups associated with the Load Balancer
variable "security_groups" {
  description = "Security groups for the Load Balancer"
  type        = list(string)
}

# Variable for the subnets associated with the Load Balancer
variable "subnets" {
  description = "Subnets for the Load Balancer"
  type        = list(string)
}

# Variable for the idle timeout of the Load Balancer
variable "idle_timeout" {
  description = "Idle timeout for the Load Balancer"
  type        = number
  default     = 60
}

# Variable for the tags to apply to resources
variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Variable for the domain name of the ACM certificate
variable "acm_certificate_domain" {
  description = "Domain name for the ACM certificate"
  type        = string
}

# Variable for the name of the Target Group
variable "target_group_name" {
  description = "Name of the Target Group"
  type        = string
}

# Variable for the port of the Target Group
variable "target_port" {
  description = "Port for the Target Group"
  type        = number
}

# Variable for the protocol of the Target Group
variable "target_protocol" {
  description = "Protocol for the Target Group"
  type        = string
}

# Variable for the VPC ID associated with the Target Group
variable "vpc_id" {
  description = "VPC ID for the Target Group"
  type        = string
}

# Variable for the target type (e.g., instance, ip, lambda)
variable "target_type" {
  description = "Target type (e.g., instance, ip, lambda)"
  type        = string
  default     = "instance"
}

# Variable to enable or disable health checks
variable "health_check_enabled" {
  description = "Enable health checks"
  type        = bool
  default     = true
}

# Variable for the path of the health check
variable "health_check_path" {
  description = "Path for the health check"
  type        = string
}

# Variable for the port of the health check
variable "health_check_port" {
  description = "Port for the health check"
  type        = string
}

# Variable for the protocol of the health check
variable "health_check_protocol" {
  description = "Protocol for the health check"
  type        = string
}

# Variable for the matcher of the health check (e.g., 200)
variable "health_check_matcher" {
  description = "Health check matcher (e.g., 200)"
  type        = string
}

# Variable for the interval between health checks
variable "health_check_interval" {
  description = "Interval between health checks"
  type        = number
  default     = 30
}

# Variable for the timeout of the health check
variable "health_check_timeout" {
  description = "Timeout for health checks"
  type        = number
  default     = 5
}

# Variable for the healthy threshold of the health check
variable "health_check_healthy_threshold" {
  description = "Healthy threshold for health checks"
  type        = number
  default     = 3
}

# Variable for the unhealthy threshold of the health check
variable "health_check_unhealthy_threshold" {
  description = "Unhealthy threshold for health checks"
  type        = number
  default     = 2
}

# Variable for the port of the Listener
variable "listener_port" {
  description = "Port for the Listener"
  type        = number
  default     = 443
}

# Variable for the protocol of the Listener
variable "listener_protocol" {
  description = "Protocol for the Listener"
  type        = string
  default     = "HTTPS"
}

# Variable for the SSL policy of the Listener
variable "ssl_policy" {
  description = "SSL policy for the Listener"
  type        = string
  default     = "ELBSecurityPolicy-2016-08"
}