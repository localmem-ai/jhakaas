variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "location" {
  description = "Location for the Artifact Registry repository (e.g., us-central1)"
  type        = string
}

variable "repository_id" {
  description = "ID of the repository (name)"
  type        = string
}

variable "description" {
  description = "Description of the repository"
  type        = string
  default     = "Docker images for LocalMem application"
}

variable "labels" {
  description = "Labels to apply to the repository"
  type        = map(string)
  default     = {}
}

variable "github_actions_service_account" {
  description = "GitHub Actions service account (format: serviceAccount:name@project.iam.gserviceaccount.com)"
  type        = string
  default     = ""
}

variable "worker_service_account" {
  description = "Worker service account (format: serviceAccount:name@project.iam.gserviceaccount.com)"
  type        = string
  default     = ""
}

variable "cloudbuild_service_account" {
  description = "Cloud Build service account for pushing images (format: serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com)"
  type        = string
  default     = ""
}
