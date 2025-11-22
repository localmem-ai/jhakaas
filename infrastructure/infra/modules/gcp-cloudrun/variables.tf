variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "service_name" {
  type = string
}

variable "image" {
  type = string
}

variable "service_account" {
  type = string
}

variable "env_vars" {
  type    = map(string)
  default = {}
}

variable "secrets" {
  type    = map(string)
  default = {}
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "port" {
  type    = number
  default = 8080
}

variable "timeout_seconds" {
  type    = number
  default = 300
}

variable "min_instances" {
  type    = number
  default = 0
}

variable "max_instances" {
  type    = number
  default = 2
}

variable "allow_unauthenticated" {
  type    = bool
  default = true
}

variable "vpc_connector" {
  type        = string
  default     = null
  description = "VPC connector name for private network access"
}

variable "vpc_egress" {
  type        = string
  default     = "PRIVATE_RANGES_ONLY"
  description = "VPC egress setting (ALL_TRAFFIC or PRIVATE_RANGES_ONLY)"
}

variable "cloud_sql_instances" {
  type        = list(string)
  default     = []
  description = "List of Cloud SQL instance connection names for Cloud SQL Proxy"
}

variable "gpu_count" {
  type        = string
  default     = "0"
  description = "Number of GPUs to allocate (0 or 1)"
}

variable "launch_stage" {
  type        = string
  default     = "GA"
  description = "Launch stage (GA, BETA, ALPHA). Required for GPU."
}

variable "additional_annotations" {
  type        = map(string)
  default     = {}
  description = "Additional annotations for the service"
}

variable "gcs_volumes" {
  type = list(object({
    name        = string
    bucket_name = string
    mount_path  = string
    read_only   = bool
  }))
  default     = []
  description = "List of GCS buckets to mount as volumes"
}

variable "ingress" {
  type        = string
  default     = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  description = "Ingress settings: INGRESS_TRAFFIC_ALL, INGRESS_TRAFFIC_INTERNAL_ONLY, INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
}
