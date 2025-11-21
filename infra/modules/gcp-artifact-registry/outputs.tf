output "repository_id" {
  description = "ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.repository.repository_id
}

output "repository_name" {
  description = "Full name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.repository.name
}

output "repository_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.location}-docker.pkg.dev/${var.project_id}/${var.repository_id}"
}
