# FastAPI Starter Kit - RabbitMQ Service

[RabbitMQ](https://www.rabbitmq.com/) is an open source message broker that enables inter-service communication in the microservices architecture. The FastAPI Starter Kit uses RabbitMQ for RPC-style communication between services.

**Features:**
- Message broker for microservices communication
- RPC pattern support for synchronous service calls
- Queue management for task distribution
- Management UI for monitoring and administration
- **Dead Letter Exchange (DLX) and Dead Letter Queue (DLQ)** for failed messages (see below)

**Dead Letter Queues (DLQ):** The data service (and backend `EventReceiver`) declare a DLX and DLQ per main queue (e.g. `data_queue_dlx`, `data_queue_dlq`). When processing fails, the consumer rejects the message with `requeue=False`, so RabbitMQ routes it to the DLQ for inspection or retry. In the Management UI (Queues tab) you will see the main queue plus `data_queue_dlq`. If the main queue already existed without DLQ args, delete it once so it can be recreated with dead-letter arguments.

## Instructions

To run all services, check instructions in main [README](../README.md)

#### Running RabbitMQ service locally

1. Run Docker Compose script

```
docker-compose up --build -d
```

2. RabbitMQ dashboard

```
http://localhost:15672 (guest/welcome1)
```

#### Build and run Kubernetes Pod

Instructions are based on content explained by [That DevOps Guy](https://www.youtube.com/c/MarcelDempers)

1. Create namespace

```
kubectl create ns rabbits
```

2. Check storage class

```
kubectl get storageclass
```

3. Define RabbitMQ role mappings

```
kubectl apply -n rabbits -f rabbit-rbac.yaml
```

4. Define RabbitMQ secret

```
kubectl apply -n rabbits -f rabbit-secret.yaml
```

5. Define RabbitMQ configs

```
kubectl apply -n rabbits -f rabbit-configmap.yaml
```

6. Create RabbitMQ cluster and pods

```
kubectl apply -n rabbits -f rabbit-statefulset.yaml
```

7. Verify pods

```
kubectl -n rabbits get pods
```

8. Verify assigned persistence volumes

```
kubectl -n rabbits get pvc
```

9. Open external access, to access RabbitMQ UI

```
kubectl -n rabbits port-forward rabbitmq-0 15672:15672
```

10. RabbitMQ UI URL

```
http://localhost:15672/ (guest/welcome1)
```

11. Scale RabbitMQ cluster

```
kubectl scale -n rabbits statefulsets rabbitmq --replicas=2
```

12. Delete all resources

```
kubectl delete all --all -n rabbits
```

## Default Configuration

- **Port**: 5672 (AMQP), 15672 (Management UI)
- **Username**: `guest`
- **Password**: `welcome1`
- **Default Queue**: `data_queue`

## Usage in FastAPI Starter Kit

RabbitMQ is used for:
1. **Inter-service communication**: API service communicates with data service via RabbitMQ RPC pattern
2. **Queue management**: Services listen to specific queues for incoming requests
3. **Message routing**: RabbitMQ routes messages to appropriate service consumers

Services use `kombu` library to interact with RabbitMQ, providing a high-level abstraction for messaging.

## Structure

```
.
├── Dockerfile
├── init.sh
├── rabbit-configmap.yaml      # RabbitMQ configuration
├── rabbit-rbac.yaml           # Role-based access control
├── rabbit-secret.yaml         # Credentials secret
├── rabbit-statefulset.yaml    # Kubernetes StatefulSet
└── README.MD
```

## License

Licensed under the Apache License, Version 2.0.
