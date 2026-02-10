kubectl delete all --all -n fastapi-starter

kubectl delete all --all -n rabbits

kubectl delete all --all -n ingress-nginx

kubectl delete -n fastapi-starter -f backend/backend-ingress.yaml

# Note: Add data service cleanup here when Kubernetes YAML is created
# kubectl delete -n fastapi-starter -f services/dataservice/dataservice-pod.yaml
