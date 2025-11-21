# Outputs for GCP Storage Module

output "bucket_name" {
  description = "The name of the bucket"
  value       = google_storage_bucket.bucket.name
}

output "bucket_url" {
  description = "The bucket URL"
  value       = google_storage_bucket.bucket.url
}

output "bucket_self_link" {
  description = "The bucket self link"
  value       = google_storage_bucket.bucket.self_link
}
