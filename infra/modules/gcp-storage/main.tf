# GCP Storage Module
# Creates GCS buckets with lifecycle policies and IAM bindings

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

# GCS Bucket
resource "google_storage_bucket" "bucket" {
  name     = var.bucket_name
  location = var.location
  project  = var.project_id

  storage_class               = var.storage_class
  uniform_bucket_level_access = true
  public_access_prevention    = var.public_access_prevention

  versioning {
    enabled = var.versioning_enabled
  }

  # Lifecycle rules
  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules

    content {
      action {
        type          = lifecycle_rule.value.action
        storage_class = lookup(lifecycle_rule.value, "storage_class", null)
      }

      condition {
        age                   = lookup(lifecycle_rule.value.condition, "age", null)
        num_newer_versions    = lookup(lifecycle_rule.value.condition, "num_newer_versions", null)
        with_state            = lookup(lifecycle_rule.value.condition, "with_state", null)
        matches_storage_class = lookup(lifecycle_rule.value.condition, "matches_storage_class", null)
        matches_prefix        = lookup(lifecycle_rule.value.condition, "matches_prefix", null)
        matches_suffix        = lookup(lifecycle_rule.value.condition, "matches_suffix", null)
      }
    }
  }

  # Encryption (optional - uses Google-managed keys by default)
  dynamic "encryption" {
    for_each = var.encryption_key != null ? [1] : []

    content {
      default_kms_key_name = var.encryption_key
    }
  }

  # CORS configuration (optional)
  dynamic "cors" {
    for_each = var.cors_config != null ? [var.cors_config] : []

    content {
      origin          = cors.value.origin
      method          = cors.value.method
      response_header = lookup(cors.value, "response_header", [])
      max_age_seconds = lookup(cors.value, "max_age_seconds", 3600)
    }
  }

  labels = var.labels

  # Force destroy (use carefully - only for dev environments)
  force_destroy = var.force_destroy
}

# IAM bindings
resource "google_storage_bucket_iam_binding" "bindings" {
  for_each = var.iam_bindings

  bucket = google_storage_bucket.bucket.name
  role   = each.key

  members = each.value
}
