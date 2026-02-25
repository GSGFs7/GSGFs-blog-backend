#!/usr/bin/bash
# k3s deployment script

set -e

# Set deployment environment (dev or prod)
DEPLOY_ENV=${1:-prod}

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    # Use allexport to export all variables defined in .env
    set -a
    source .env
    set +a
else
    echo "Warning: .env file not found. Variables might not be substituted correctly."
fi

# Set image registry based on deployment environment
if [ "$DEPLOY_ENV" = "dev" ]; then
    echo "Setting up development environment configuration..."
    export REGISTRY_DOMAIN=localhost
    export IMAGE_PULL_POLICY=Never
else
    echo "Setting up production environment configuration..."
    export REGISTRY_DOMAIN=${REGISTRY_DOMAIN}
    export IMAGE_PULL_POLICY=Always
fi

echo "Image registry: $REGISTRY_DOMAIN"
echo "Image pull policy: $IMAGE_PULL_POLICY"

echo "Deploying to k3s cluster..."
echo ""

# Apply configuration files in order
echo "1. Creating namespace..."
kubectl apply -f .config/k8s/namespace.yaml
echo ""

echo "2. Creating configmap and secrets..."
kubectl apply -f .config/k8s/configmap.yaml
# Use envsubst to substitute variables in the secret template
envsubst < .config/k8s/secret.example.yaml | kubectl apply -f -
echo ""

echo "3. Creating PVC for model cache..."
kubectl apply -f .config/k8s/pvc.yaml
echo ""

echo "4. Deploying PostgreSQL..."
kubectl apply -f .config/k8s/postgres.yaml
echo ""

echo "5. Deploying Redis..."
kubectl apply -f .config/k8s/redis.yaml
echo ""

echo "6. Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=blog-postgres -n blog --timeout=300s
kubectl wait --for=condition=available deployment/blog-redis -n blog --timeout=300s
echo ""

echo "7. Running database migrations..."
# Delete existing job if it exists to allow updates to job spec (which is immutable)
kubectl delete job blog-django-migrate -n blog --ignore-not-found
envsubst < .config/k8s/job-migrate.yaml | kubectl apply -f -
echo ""

echo "8. Waiting for migrations to complete..."
kubectl wait --for=condition=complete --timeout=300s job/blog-django-migrate -n blog
echo ""

echo "9. Deploying Django application..."
envsubst < .config/k8s/django.yaml | kubectl apply -f -
echo ""

echo "10. Deploying Celery Worker..."
envsubst < .config/k8s/celery-worker.yaml | kubectl apply -f -
echo ""

echo "11. Deploying Celery Beat..."
envsubst < .config/k8s/celery-beat.yaml | kubectl apply -f -
echo ""

echo "12. Deploying Backup CronJob..."
envsubst < .config/k8s/job-backup.yaml | kubectl apply -f -
echo ""

echo "13. Deploying Ingress..."
if [ "$DEPLOY_ENV" = "dev" ]; then
    echo "Using development environment Ingress configuration..."
    envsubst < .config/k8s/ingress-dev.yaml | kubectl apply -f -
else
    echo "Using production environment Ingress configuration..."
    envsubst < .config/k8s/clusterissuer.yaml | kubectl apply -f -
    envsubst < .config/k8s/ingress.yaml | kubectl apply -f -
fi

echo ""
echo "Deployment completed!"
echo ""
echo "Check deployment status:"
echo "  kubectl get -n blog pods"
echo "  kubectl get -n blog svc"
echo "  kubectl get -n blog ingress"
echo "  kubectl get -n blog cronjob"
echo ""
echo "View logs:"
echo "  kubectl logs -f -n blog deployment/blog-django"
echo "  kubectl logs -f -n blog deployment/blog-celery-worker"
echo "  kubectl logs -f -n blog deployment/blog-celery-beat"
