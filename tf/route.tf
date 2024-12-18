# Root domain record (pika-card.store)
resource "aws_route53_record" "app_dns" {
  zone_id = "Z0057660LWNAO0YHSRYG"  # The ID of the hosted zone
  name    = "pika-card.store"       # The domain name
  type    = "A"                     # The record type
  ttl     = 300                     # Time-to-live in seconds


  alias {
    name                   = aws_lb.app_lb.dns_name  # The DNS name of the load balancer
    zone_id                = aws_lb.app_lb.zone_id   # The zone ID of the load balancer
    evaluate_target_health = true                    # Whether to evaluate the health of the target
  }
}

# WWW subdomain record (www.pika-card.store)
resource "aws_route53_record" "app_www_dns" {
  zone_id = "Z0057660LWNAO0YHSRYG"  # The ID of the hosted zone
  name    = "www.pika-card.store"   # The subdomain name
  type    = "A"                     # The record type
  ttl     = 300                     # Time-to-live in seconds


  alias {
    name                   = aws_lb.app_lb.dns_name  # The DNS name of the load balancer
    zone_id                = aws_lb.app_lb.zone_id   # The zone ID of the load balancer
    evaluate_target_health = true                    # Whether to evaluate the health of the target
  }
}