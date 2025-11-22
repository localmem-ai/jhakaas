# Google Artifact Registry Repository
# Used for storing Docker images for server and worker containers

resource "google_artifact_registry_repository" "repository" {
  location      = var.location
  repository_id = var.repository_id
  description   = var.description
  format        = "DOCKER"
  project       = var.project_id

  labels = var.labels
}

# IAM binding to allow GitHub Actions service account to push images
resource "google_artifact_registry_repository_iam_member" "github_actions_writer" {
  count = var.github_actions_service_account != "" ? 1 : 0

  project    = var.project_id
  location   = var.location
  repository = google_artifact_registry_repository.repository.name
  role       = "roles/artifactregistry.writer"
  member     = var.github_actions_service_account
}

# IAM binding to allow worker service account to pull images
resource "google_artifact_registry_repository_iam_member" "worker_reader" {
  count = var.worker_service_account != "" ? 1 : 0

  project    = var.project_id
  location   = var.location
  repository = google_artifact_registry_repository.repository.name
  role       = "roles/artifactregistry.reader"
  member     = var.worker_service_account
}

# IAM binding to allow Cloud Build (Compute Engine SA) to push images
resource "google_artifact_registry_repository_iam_member" "cloudbuild_writer" {
  count = var.cloudbuild_service_account != "" ? 1 : 0

  project    = var.project_id
  location   = var.location
  repository = google_artifact_registry_repository.repository.name
  role       = "roles/artifactregistry.writer"
  member     = var.cloudbuild_service_account
}
