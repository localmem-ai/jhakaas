variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "jhakaas-dev"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-southeast1"
}

variable "worker_image" {
  description = "Docker image for the worker"
  type        = string
  default     = "asia-southeast1-docker.pkg.dev/jhakaas-dev/jhakaas-repo/worker:latest"
}
