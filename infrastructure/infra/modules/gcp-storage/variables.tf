# Variables for GCP Storage Module

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "bucket_name" {
  description = "Name of the GCS bucket (must be globally unique)"
  type        = string
}

variable "location" {
  description = "Bucket location (region or multi-region)"
  type        = string
  default     = "US-CENTRAL1"
}

variable "storage_class" {
  description = "Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)"
  type        = string
  default     = "STANDARD"
}

variable "versioning_enabled" {
  description = "Enable object versioning"
  type        = bool
  default     = false
}

variable "public_access_prevention" {
  description = "Public access prevention (inherited or enforced)"
  type        = string
  default     = "inherited"
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules"
  type = list(object({
    action        = string
    storage_class = optional(string)
    condition = object({
      age                   = optional(number)
      num_newer_versions    = optional(number)
      with_state            = optional(string)
      matches_storage_class = optional(list(string))
      matches_prefix        = optional(list(string))
      matches_suffix        = optional(list(string))
    })
  }))
  default = []
}

variable "encryption_key" {
  description = "KMS key for encryption (null for Google-managed)"
  type        = string
  default     = null
}

variable "cors_config" {
  description = "CORS configuration"
  type = object({
    origin          = list(string)
    method          = list(string)
    response_header = optional(list(string))
    max_age_seconds = optional(number)
  })
  default = null
}

variable "iam_bindings" {
  description = "Map of role to list of members"
  type        = map(list(string))
  default     = {}
}

variable "labels" {
  description = "Labels to apply to the bucket"
  type        = map(string)
  default     = {}
}

variable "force_destroy" {
  description = "Allow bucket deletion even if not empty (use carefully!)"
  type        = bool
  default     = false
}
