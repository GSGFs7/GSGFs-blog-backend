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
    echo "Login success!"
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
    buildah pull "$cache_ref" || true

    # build image
    local target_arg=""
    if [ -n "$target" ]; then target_arg="--target $target"; fi

    echo "Building $name using buildah bud..."
    # 'bud' is 'build-using-dockerfile'
    buildah bud "$target_arg" \
        --cache-from "$cache_ref" \
        --build-arg "hf_token=$HUGGINGFACE_HUB_TOKEN" \
        -f "$dockerfile" \
        -t "localhost/blog-$name:latest" .
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
    buildah_login
    build_images
    push_images
}

main
