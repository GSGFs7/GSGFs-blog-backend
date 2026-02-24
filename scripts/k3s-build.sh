#!/usr/bin/bash
# k3s component build script

set -e

# Build Model Downloader image
echo "Building Model Downloader image..."
docker build \
    -f .config/k8s/containers/model-downloader.Dockerfile \
    -t localhost/blog-model-downloader:latest .

# Build Django application image
echo "Building Django application image..."
docker build \
    -f .config/k8s/containers/django.Dockerfile \
    -t localhost/blog-django:latest .

# Build Celery Worker image
echo "Building Celery Worker image..."
docker build \
    -f .config/k8s/containers/celery-worker.Dockerfile \
    -t localhost/blog-celery-worker:latest .

# Build Celery Beat image
echo "Building Celery Beat image..."
docker build \
    -f .config/k8s/containers/celery-beat.Dockerfile \
    -t localhost/blog-celery-beat:latest .
echo "All images built successfully!"
echo ""

for image in model-downloader blog-django blog-celery-worker blog-celery-beat; do
    echo "Importing localhost/$image:latest to k3s..."
    docker save localhost/$image:latest | sudo k3s ctr images import -
done
echo ""
echo "Images imported successfully!"
echo ""
echo "Deploy to k3s:"
echo "  ./scripts/k3s-deploy.sh"
