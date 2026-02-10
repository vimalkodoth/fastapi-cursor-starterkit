# RabbitMQ namespace and service

{
  kubectl create ns rabbits
} || {
  echo 'rabbits namespace is already defined'
}

kubectl apply -n rabbits -f rabbitmq/rabbit-rbac.yaml

kubectl apply -n rabbits -f rabbitmq/rabbit-secret.yaml

kubectl apply -n rabbits -f rabbitmq/rabbit-configmap.yaml

kubectl apply -n rabbits -f rabbitmq/rabbit-statefulset.yaml

kubectl rollout status -n rabbits statefulset.apps/rabbitmq

kubectl get -n rabbits pods

kubectl get -n rabbits svc

kubectl get -n rabbits pvc

# FastAPI Starter namespace

{
  kubectl create ns fastapi-starter
} || {
  echo 'fastapi-starter namespace is already defined'
}

# Logger Service

kubectl apply -n fastapi-starter -f logger/logger-pod.yaml

kubectl rollout status -n fastapi-starter deploy/logger-service

kubectl get -n fastapi-starter pods

kubectl get -n fastapi-starter svc logger-service

kubectl get -n fastapi-starter deployments

# FastAPI Application

kubectl apply -n fastapi-starter -f backend/backend-pod.yaml

kubectl rollout status -n fastapi-starter deploy/fastapi-api

kubectl get -n fastapi-starter pods

kubectl get -n fastapi-starter svc fastapi-api

kubectl get -n fastapi-starter deployments

# FastAPI Celery Worker

kubectl apply -n fastapi-starter -f backend/backend-celery-pod.yaml

kubectl rollout status -n fastapi-starter deploy/fastapi-api-celery

kubectl get -n fastapi-starter pods

kubectl get -n fastapi-starter deployments

# FastAPI Ingress

kubectl apply -n fastapi-starter -f backend/backend-ingress.yaml

# Data Service

# Note: Add data service deployment here when Kubernetes YAML is created
# kubectl apply -n fastapi-starter -f services/dataservice/dataservice-pod.yaml
# kubectl rollout status -n fastapi-starter deploy/data-service
# kubectl get -n fastapi-starter pods
# kubectl get -n fastapi-starter deployments
