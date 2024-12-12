module "ec2_instance" {
  source          = "./modules/nat-instance"
  ami_id          = "ami-0fcbdd3ee4f67a0a0"
  instance_type   = "t3.micro"
  key_name        = "kafka"
  subnet_id       = aws_subnet.public_zone1.id
  security_group  = aws_security_group.nat_bastion_sg.id
  instance_name   = "NAT-Bastion-Instance"
  vpc_id          = aws_vpc.main.id
}

resource "aws_route" "nat_route" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = module.ec2_instance.nat_instance_network_interface_id

  lifecycle {
    create_before_destroy = false
    prevent_destroy       = false
  }
  depends_on = [module.ec2_instance]


}



