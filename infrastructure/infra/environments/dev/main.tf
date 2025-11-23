terraform {
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

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# 1. Artifact Registry (To store Docker images)
module "artifact_registry" {
  source      = "../../modules/gcp-artifact-registry"
  project_id  = var.project_id
  location    = var.region
  repository_id = "jhakaas-repo"
  description   = "Docker repository for Jhakaas"
}

# 2. GCS Bucket for Models (Read-only for worker)
module "models_bucket" {
  source            = "../../modules/gcp-storage"
  project_id        = var.project_id
  bucket_name       = "jhakaas-models-${var.project_id}"
  location          = var.region
  force_destroy     = false
  versioning_enabled = false
}

# 3. GCS Bucket for User Images
module "images_bucket" {
  source            = "../../modules/gcp-storage"
  project_id        = var.project_id
  bucket_name       = "jhakaas-images-${var.project_id}"
  location          = var.region
  force_destroy     = false
  versioning_enabled = false
}

# Service Account for Worker
resource "google_service_account" "worker_sa" {
  account_id   = "jhakaas-worker-sa"
  display_name = "Jhakaas Worker Service Account"
}

# Grant Worker access to read Models
resource "google_storage_bucket_iam_member" "worker_read_models" {
  bucket = module.models_bucket.bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.worker_sa.email}"
}

# Grant Worker access to write Images
resource "google_storage_bucket_iam_member" "worker_write_images" {
  bucket = module.images_bucket.bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.worker_sa.email}"
}

# 4. Cloud Run Worker (GPU)
module "worker_service" {
  source         = "../../modules/gcp-cloudrun"
  service_name   = "jhakaas-worker"
  project_id     = var.project_id
  region         = var.region
  image          = var.worker_image
  service_account = google_service_account.worker_sa.email

  # Network Config (Dev: allow direct access with IAM)
  ingress        = "INGRESS_TRAFFIC_ALL"

  # GPU Config (L4)
  cpu            = "4"        # 4 vCPU required for GPU
  memory         = "16Gi"     # 16GB RAM
  gpu_count      = "1"
  launch_stage   = "BETA"
  min_instances  = 0  # Scale to zero to save costs (cold start ~8-10min)
  max_instances  = 1  # Single instance to avoid zonal redundancy
  timeout_seconds = 900  # 15 minutes for AI model generation

  # Startup probe for model loading (takes 8-10 minutes)
  # Total timeout: 5 attempts × 5 minutes = 25 minutes
  startup_probe_enabled          = true
  startup_probe_initial_delay    = 0
  startup_probe_timeout          = 240  # 4 minutes per check
  startup_probe_period           = 300  # 5 minutes between checks
  startup_probe_failure_threshold = 5   # 5 attempts before giving up

  # Annotations
  additional_annotations = {
    "run.googleapis.com/cpu-throttling" = "false" # Always on for GPU
    "run.googleapis.com/startup-cpu-boost" = "true" # CPU boost during startup
  }
  
  env_vars = {
    "MODEL_BUCKET"  = module.models_bucket.bucket_name
    "IMAGES_BUCKET" = module.images_bucket.bucket_name
  }

  # Mount models bucket as volume for fast access
  gcs_volumes = [{
    name        = "models"
    bucket_name = module.models_bucket.bucket_name
    mount_path  = "/gcs/models"
    read_only   = true
  }]
}

# 5. Cloud Build Service Account Permissions
# Grant Compute Engine default service account (used by Cloud Build) access to Artifact Registry
resource "google_project_iam_member" "compute_artifactregistry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "compute_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant Cloud Build permission to deploy to Cloud Run
resource "google_project_iam_member" "compute_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant Cloud Build permission to act as the worker service account
resource "google_service_account_iam_member" "compute_act_as_worker" {
  service_account_id = google_service_account.worker_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Get project number for service accounts
data "google_project" "project" {
  project_id = var.project_id
}

# 6. IAM: Allow Cloud Functions to invoke the worker
# Cloud Functions use the App Engine default service account
# Uncomment this after deploying Cloud Functions (which creates the service account)
/*
resource "google_cloud_run_service_iam_member" "functions_invoke_worker" {
  service  = module.worker_service.service_name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.project_id}@appspot.gserviceaccount.com"
}
*/
