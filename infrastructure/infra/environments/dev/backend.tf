terraform {
  backend "gcs" {
    bucket = "jhakaas-tf-state-jhakaas-dev"
    prefix = "dev"
  }
}
