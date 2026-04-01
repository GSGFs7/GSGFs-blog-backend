#!/usr/bin/env bash
# build and push images to registry
# used by Woodpecker CI with buildah (rootless/vfs mode)

set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

COMMIT_HASH="${CI_COMMIT_SHA:-latest}"

declare -a IMAGES=(
    ".config/k8s/containers/app.Dockerfile:django:django"
    ".config/k8s/containers/app.Dockerfile:worker:celery-worker"
    ".config/k8s/containers/app.Dockerfile:beat:celery-beat"
    ".config/k8s/containers/app.Dockerfile:downloader:model-downloader"
    ".config/k8s/containers/backup.Dockerfile::backup"
)
CACHE_IMAGE_PREFIX="$REGISTRY_DOMAIN/blog-buildcache"

function buildah_login() {
    echo "Logging into $REGISTRY_DOMAIN..."
    buildah login -u "$REGISTRY_USERNAME" -p "$REGISTRY_PASSWORD" "$REGISTRY_DOMAIN"
}

function _build_with_buildah() {
    local name=$1
    local dockerfile=$2
    local target=$3

    # building cache
    local cache_ref=""
    if [[ "$dockerfile" == *"app.Dockerfile"* ]]; then
        cache_ref="${CACHE_IMAGE_PREFIX}:app"
    else
        cache_ref="${REGISTRY_DOMAIN}/blog-$name:latest"
    fi

    echo "Attempting to pull cache from $cache_ref..."
    # Suppress error output for pull as it might fail if cache doesn't exist or is incompatible
    local has_cache=false
    if buildah pull "$cache_ref" 2> /dev/null; then
        has_cache=true
    fi

    # build image
    local build_args=(
        "bud"
        "--layers"
        "-f" "$dockerfile"
        "-t" "localhost/blog-$name:latest"
    )

    if [ "$has_cache" = true ]; then
        # Use the local image ID to avoid "repository must contain neither a tag nor digest" errors
        local cache_id=$(buildah images -q "$cache_ref" | head -n 1)
        if [ -n "$cache_id" ]; then
            echo "Using local cache ID: $cache_id"
            build_args+=("--cache-from" "$cache_id")
        fi
    fi

    if [ -n "$target" ]; then
        build_args+=("--target" "$target")
    fi

    echo "Building $name using buildah bud..."
    # 'bud' is 'build-using-dockerfile'
    buildah "${build_args[@]}" .
}

function build_images() {
    echo "Building all images..."
    for image_info in "${IMAGES[@]}"; do
        IFS=':' read -r dockerfile target name <<< "$image_info"
        _build_with_buildah "$name" "$dockerfile" "$target"
    done
    echo "All images built successfully!"
}

function push_images() {
    echo "Pushing images to registry..."
    for image_info in "${IMAGES[@]}"; do
        IFS=':' read -r dockerfile target name <<< "$image_info"
        local remote_tag_latest="$REGISTRY_DOMAIN/blog-$name:latest"
        local remote_tag_sha="$REGISTRY_DOMAIN/blog-$name:$COMMIT_HASH"

        buildah tag "localhost/blog-$name:latest" "$remote_tag_latest"
        buildah tag "localhost/blog-$name:latest" "$remote_tag_sha"

        echo "Pushing $name..."
        # just test do not push
        # buildah push "$remote_tag_latest"
        # buildah push "$remote_tag_sha"

        # Update app-level cache if django component succeeded
        if [[ "$dockerfile" == *"app.Dockerfile"* && "$name" == "django" ]]; then
            buildah tag "localhost/blog-$name:latest" "${CACHE_IMAGE_PREFIX}:app"
            buildah push "${CACHE_IMAGE_PREFIX}:app"
        fi
    done
}

function main() {
    buildah info
    buildah_login
    build_images
    push_images
}

main
