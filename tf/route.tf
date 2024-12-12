# Root domain record (pika-card.store)
resource "aws_route53_record" "app_dns" {
  zone_id = "Z0057660LWNAO0YHSRYG"
  name    = "pika-card.store"
  type    = "A"

  alias {
    name                   = aws_lb.app_lb.dns_name
    zone_id                = aws_lb.app_lb.zone_id
    evaluate_target_health = true
  }
}

# WWW subdomain record (www.pika-card.store)
resource "aws_route53_record" "app_www_dns" {
  zone_id = "Z0057660LWNAO0YHSRYG"
  name    = "www.pika-card.store"
  type    = "A"

  alias {
    name                   = aws_lb.app_lb.dns_name
    zone_id                = aws_lb.app_lb.zone_id
    evaluate_target_health = true
  }
}
