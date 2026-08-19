variable "REGISTRY" {
  default = "harbor.sun-asterisk.vn"
}

variable "PREFIX" {
  default = "dps/s-staff-docs"
}

variable "TAG" {
  default = "latest"
}

variable "TAGS" {
  default = TAG
}

function "format_tags" {
  params = [component, tags]
  result = formatlist("${REGISTRY}/${PREFIX}/%s:%s", component, tags)
}

target "docker-metadata-action" {}

target "_common" {
  tags    = coalesce(target.docker-metadata-action.tags, split(",", TAGS))
  labels  = target.docker-metadata-action.labels
  context = "."
}

target "app" {
  inherits   = ["_common"]
  dockerfile = "Dockerfile"
  tags       = format_tags("ai/cv-matching", target._common.tags)
  labels = {
    "org.opencontainers.image.description" = "CV Matching API"
  }
}

group "default" {
  targets = ["app"]
}
