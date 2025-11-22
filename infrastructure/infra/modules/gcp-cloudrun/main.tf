# GCP Cloud Run Module
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }
}

resource "google_cloud_run_v2_service" "service" {
  provider     = google-beta  # Required for GPU support
  name         = var.service_name
  location     = var.region
  project      = var.project_id
  launch_stage = var.launch_stage

  # Ingress controls where traffic can come from
  # INGRESS_TRAFFIC_ALL: Direct internet access (dev)
  # INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER: Only via load balancers (prod)
  # INGRESS_TRAFFIC_INTERNAL_ONLY: Only from VPC networks (most restrictive)
  ingress = var.ingress

  template {
    service_account = var.service_account

    # GPU zonal redundancy must be disabled for single-instance GPU workloads
    gpu_zonal_redundancy_disabled = var.gpu_count != "0" ? true : null

    dynamic "vpc_access" {
      for_each = var.vpc_connector != null && var.vpc_connector != "" ? [1] : []
      content {
        connector = var.vpc_connector
        egress    = var.vpc_egress
      }
    }

    # Cloud SQL Proxy connections and other annotations
    annotations = merge(
      length(var.cloud_sql_instances) > 0 ? {
        "run.googleapis.com/cloudsql-instances" = join(",", var.cloud_sql_instances)
      } : {},
      var.additional_annotations
    )

    containers {
      image = var.image

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      resources {
        limits = merge(
          {
            cpu    = var.cpu
            memory = var.memory
          },
          var.gpu_count != "0" ? { "nvidia.com/gpu" = var.gpu_count } : {}
        )
      }

      ports {
        container_port = var.port
      }

      dynamic "volume_mounts" {
        for_each = var.gcs_volumes
        content {
          name       = volume_mounts.value.name
          mount_path = volume_mounts.value.mount_path
        }
      }
    }

    dynamic "volumes" {
      for_each = var.gcs_volumes
      content {
        name = volumes.value.name
        gcs {
          bucket    = volumes.value.bucket_name
          read_only = volumes.value.read_only
        }
      }
    }

    # Node selector for GPU (required for GPU workloads)
    # Only include this block if GPU is requested
    node_selector {
      accelerator = var.gpu_count != "0" ? "nvidia-l4" : null
    }

    timeout = "${var.timeout_seconds}s"

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Public access via IAM binding
# For Jhakaas: Cloud Functions will invoke the worker, not a load balancer
# Cloud Functions use the App Engine default service account: PROJECT_ID@appspot.gserviceaccount.com
# Grant that service account roles/run.invoker permission after Cloud Functions are deployed
/*
resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  service  = google_cloud_run_v2_service.service.name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}
*/
