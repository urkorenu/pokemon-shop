# Output the network interface ID of the NAT instance
output "network_interface_id" {
  value = aws_instance.nat_instance.primary_network_interface_id
}