# Reference an existing S3 bucket
data "aws_s3_bucket" "pokemon_pics" {
  bucket = "pokemon--pics" # Name of the existing bucket
}

# Uncomment the following resource block to create a new S3 bucket
# resource "aws_s3_bucket" "pokemon_pics" {
#   bucket = "pokemon-pics2"
#
#   tags = {
#     Name        = "Pokemon Pics"
#     Environment = "Dev"
#   }
# }

resource "aws_s3_bucket_public_access_block" "pokemon_pics_block" {
#   bucket                  = aws_s3_bucket.pokemon_pics.id
  bucket                  = data.aws_s3_bucket.pokemon_pics.id
  block_public_acls       = false
  block_public_policy     = false # Disable to allow public bucket policies
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "pokemon_pics_policy" {
#   bucket = aws_s3_bucket.pokemon_pics.id
  bucket = data.aws_s3_bucket.pokemon_pics.id


  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = "*",
        Action    = "s3:GetObject",
        Resource  = [
#           "arn:aws:s3:::${aws_s3_bucket.pokemon_pics.id}",
#           "arn:aws:s3:::${aws_s3_bucket.pokemon_pics.id}/*"
          "arn:aws:s3:::${data.aws_s3_bucket.pokemon_pics.id}",
          "arn:aws:s3:::${data.aws_s3_bucket.pokemon_pics.id}/*"
        ]
      }
    ]
  })
}

output "s3_bucket_name" {
#   value = aws_s3_bucket.pokemon_pics.bucket
  value       = data.aws_s3_bucket.pokemon_pics.bucket
  description = "The name of the S3 bucket."
}
