#!/usr/bin/bash
# k3s component build script

set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

detect_container_builder() {
    if command -v podman &> /dev/null; then
        echo "podman"
    elif command -v docker &> /dev/null; then
        echo "docker"
    else
        echo "ERROR: Neither podman nor docker is installed" >&2
        exit 1
    fi
}

declare -a IMAGES=(
    "model-downloader:.config/k8s/containers/model-downloader.Dockerfile"
    "django:.config/k8s/containers/django.Dockerfile"
    "celery-worker:.config/k8s/containers/celery-worker.Dockerfile"
    "celery-beat:.config/k8s/containers/celery-beat.Dockerfile"
    "backup:.config/k8s/containers/backup.Dockerfile"
)

build_with_podman() {
    podman build --format oci -f "$2" -t "localhost/blog-$1:latest" .
}

build_with_docker() {
    docker buildx build --output type=oci -f "$2" -t "localhost/blog-$1:latest" .
}

build_images() {
    local builder=$1

    echo "Building images with $builder..."
    echo ""

    for image_info in "${IMAGES[@]}"; do
        IFS=':' read -r name dockerfile <<< "$image_info"
        echo "Building $name image..."
        if [ "$builder" == "podman" ]; then
            build_with_podman "$name" "$dockerfile"
        elif [ "$builder" == "docker" ]; then
            build_with_docker "$name" "$dockerfile"
        fi
    done
}

import_to_k3s() {
    local builder=$1

    echo ""
    echo "All images built successfully!"
    echo ""

    for image_info in "${IMAGES[@]}"; do
        IFS=':' read -r name dockerfile <<< "$image_info"
        echo "Importing localhost/blog-$name:latest to k3s..."
        $builder save "localhost/blog-$name:latest" | sudo k3s ctr images import -
    done
    echo ""
    echo "Images imported successfully!"
    echo ""
    echo "Deploy to k3s:"
    echo "  ./scripts/k3s-deploy.sh"
}

CONTAINER_BUILDER=$(detect_container_builder)
echo "Using $CONTAINER_BUILDER as container builder"

build_images "$CONTAINER_BUILDER"
import_to_k3s "$CONTAINER_BUILDER"
