#!/usr/bin/env bash
# build and push images to registry
# used by Woodpecker CI with podman

set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

COMMIT_HASH="${CI_COMMIT_SHA:-latest}"
REGISTRY_CERT_DIR=""
declare -a REGISTRY_REMOTE_ARGS=()

declare -a IMAGES=(
    ".config/k8s/containers/app.Dockerfile:django:django"
    ".config/k8s/containers/app.Dockerfile:worker:celery-worker"
    ".config/k8s/containers/app.Dockerfile:beat:celery-beat"
    ".config/k8s/containers/app.Dockerfile:downloader:model-downloader"
    ".config/k8s/containers/backup.Dockerfile::backup"
)

function podman_login() {
    if [ ${#REGISTRY_REMOTE_ARGS[@]} -gt 0 ]; then
        echo "Using mTLS for $REGISTRY_DOMAIN..."
        return
    fi

    echo "Logging into $REGISTRY_DOMAIN..."
    podman login -u "$REGISTRY_USERNAME" -p "$REGISTRY_PASSWORD" "$REGISTRY_DOMAIN"
}

function setup_registry_auth() {
    if [ -n "$REGISTRY_CLIENT_CERT" ] && [ -n "$REGISTRY_CLIENT_KEY" ] && [ -n "$REGISTRY_CA_CERT" ]; then
        REGISTRY_CERT_DIR="$(mktemp -d)"
        local cert_host_dir="$REGISTRY_CERT_DIR/$REGISTRY_DOMAIN"
        mkdir -p "$cert_host_dir"
        printf '%s\n' "$REGISTRY_CA_CERT" > "$cert_host_dir/ca.crt"
        printf '%s\n' "$REGISTRY_CLIENT_CERT" > "$cert_host_dir/client.cert"
        printf '%s\n' "$REGISTRY_CLIENT_KEY" > "$cert_host_dir/client.key"
        chmod 600 "$cert_host_dir/client.key"
        REGISTRY_REMOTE_ARGS=(--cert-dir "$REGISTRY_CERT_DIR")
        return
    fi

    if [ -z "$REGISTRY_USERNAME" ] || [ -z "$REGISTRY_PASSWORD" ]; then
        echo "Registry auth is not configured. Provide mTLS cert secrets or username/password." >&2
        exit 1
    fi
}

function _build_with_podman() {
    local name=$1
    local dockerfile=$2
    local target=$3

    # build image
    local build_args=(
        "build"
        "-f" "$dockerfile"
        "-t" "localhost/blog-$name:latest"
    )

    if [ -n "$target" ]; then
        build_args+=("--target" "$target")
    fi

    echo "Building $name using podman build..."
    podman "${build_args[@]}" .
}

function print_builder_info() {
    echo "Builder info:"
    podman info
}

function build_images() {
    echo "Building all images..."
    for image_info in "${IMAGES[@]}"; do
        IFS=':' read -r dockerfile target name <<< "$image_info"
        _build_with_podman "$name" "$dockerfile" "$target"
    done
    echo "All images built successfully!"
}

function push_images() {
    echo "Pushing images to registry..."
    for image_info in "${IMAGES[@]}"; do
        IFS=':' read -r dockerfile target name <<< "$image_info"
        local remote_tag_latest="$REGISTRY_DOMAIN/blog-$name:latest"
        local remote_tag_sha="$REGISTRY_DOMAIN/blog-$name:$COMMIT_HASH"

        podman tag "localhost/blog-$name:latest" "$remote_tag_latest"
        podman tag "localhost/blog-$name:latest" "$remote_tag_sha"

        # push
        echo "Pushing $name..."
        podman push "${REGISTRY_REMOTE_ARGS[@]}" "$remote_tag_latest"
        podman push "${REGISTRY_REMOTE_ARGS[@]}" "$remote_tag_sha"
    done
}

function main() {
    print_builder_info
    setup_registry_auth
    podman_login
    build_images
    push_images
}

main
