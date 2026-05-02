#!/usr/bin/env bash
# build and push images to registry
# used by Woodpecker CI

set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

COMMIT_HASH="${CI_COMMIT_SHA:-latest}"

declare -a IMAGES=(
    ".config/k8s/containers/app.Dockerfile::app"
    ".config/k8s/containers/backup.Dockerfile::backup"
)

function setup_podman_cert() {
    BASE_DIR="$HOME/.config/containers/certs.d/$REGISTRY_DOMAIN/"
    mkdir -p "$BASE_DIR"
    echo "$REGISTRY_CA_CERT" > "$BASE_DIR/ca.crt"
    echo "$REGISTRY_CLIENT_CERT" > "$BASE_DIR/client.cert"
    echo "$REGISTRY_CLIENT_KEY" > "$BASE_DIR/client.key"
    chmod 600 "$BASE_DIR/client.key"
}

function check_cdn_bypass() {
    if [ -z "${REGISTRY_IP:-}" ] || [ -z "${REGISTRY_DOMAIN:-}" ]; then
        echo "CDN bypass check failed: REGISTRY_IP or REGISTRY_DOMAIN is empty"
        exit 1
    fi

    # Verify DNS resolution (should match /etc/hosts entries)
    local resolved_ips
    resolved_ips=$(getent ahosts "$REGISTRY_DOMAIN" | awk '{print $1}' | sort -u)
    
    local found_expected_ipv4=false
    local found_blackhole_ipv6=false

    for ip in $resolved_ips; do
        if [ "$ip" == "$REGISTRY_IP" ]; then
            found_expected_ipv4=true
        elif [[ "$ip" == "::1" || "$ip" == "127.0.0.1" ]]; then
            if [[ "$ip" == "::1" ]]; then found_blackhole_ipv6=true; fi
            echo "Verified local/loopback resolution: $ip"
        else
            echo "CDN bypass check failed: Unexpected IP found (LEAK DETECTED): $ip"
            exit 1
        fi
    done

    if [ "$found_expected_ipv4" != "true" ]; then
        echo "CDN bypass check failed: Expected IPv4 $REGISTRY_IP not found in resolution."
        exit 1
    fi

    if [ "$found_blackhole_ipv6" != "true" ]; then
        echo "CDN bypass check warning: IPv6 blackhole (::1) not found. IPv6 might leak if enabled!"
    fi

    echo "DNS resolution verified: $REGISTRY_DOMAIN is locked to $REGISTRY_IP (IPv4) and ::1 (IPv6)"

    local probe_image="$REGISTRY_DOMAIN/blog-app:latest"
    local output
    local status

    echo "Checking CDN bypass with podman: $probe_image"

    set +e
    output="$(skopeo inspect "docker://$probe_image" 2>&1)"
    status=$?
    set -e

    if [ "$status" -eq 0 ]; then
        echo "CDN bypass check passed: podman can inspect $probe_image"
        return
    fi

    if printf '%s\n' "$output" | grep -Eiq "manifest unknown|name unknown"; then
        echo "CDN bypass check passed: podman reached $REGISTRY_DOMAIN, but $probe_image does not exist"
        return
    fi

    echo "CDN bypass check failed: podman could not reach $REGISTRY_DOMAIN successfully"
    printf '%s\n' "$output"
    exit 1
}

function podman_login() {
    echo "Logging into $REGISTRY_DOMAIN..."
    podman login -u "$REGISTRY_USERNAME" -p "$REGISTRY_PASSWORD" "$REGISTRY_DOMAIN"
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
        podman push "$remote_tag_latest"
        podman push "$remote_tag_sha"
    done
}

function main() {
    print_builder_info
    setup_podman_cert
    check_cdn_bypass
    #podman_login
    build_images
    push_images
}

main
