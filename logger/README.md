# FastAPI Starter Kit - Logger Service

Logger service provides observability and event tracking across the microservices architecture. It logs producer and receiver events from RabbitMQ communication, enabling request tracing and debugging.

**Features:**
- Logs producer events (when messages are sent)
- Logs receiver events (when messages are received)
- Tracks correlation IDs for request tracing
- Non-blocking background logging

## Instructions

To run all services, check instructions in main [README](../README.md)

#### Run the service without Docker

1. Install libraries

```
pip install -r requirements.txt
```

2. Start FastAPI

```
uvicorn endpoint:app --port=5001 --reload
```

3. Logger FastAPI endpoints

```
http://127.0.0.1:5001/docs
```

4. Monitor logs

```
docker logs --follow logger-service
```

#### Build and run individual container

1. Build container

```
docker build --tag logger-service .
```

2. Run container

```
docker run -it -d --name logger-service -p 5001:5001 logger-service:latest
```

3. Logger FastAPI endpoints

```
http://127.0.0.1:5001/docs
```

4. Monitor logs

```
docker logs --follow logger-service
```

#### Build and run Kubernetes Pod

1. Create namespace

```
kubectl create ns fastapi-starter
```

2. Create Pod

```
kubectl apply -n fastapi-starter -f logger-pod.yaml
```

3. Check Pod status

```
kubectl get -n fastapi-starter pods
```

4. Describe Pod

```
kubectl describe -n fastapi-starter pods logger-service
```

5. Open Pod port for testing purposes

```
kubectl port-forward -n fastapi-starter deploy/logger-service 5001:5001
```

6. Open Pod logs

```
kubectl logs -n fastapi-starter -f -l app=logger-service
```

7. Test URL

```
http://127.0.0.1:5001/docs
```

8. Check Pod service

```
kubectl get -n fastapi-starter svc logger-service
```

9. Delete Deployment

```
kubectl delete -n fastapi-starter -f logger-pod.yaml
```

10. Delete all resources

```
kubectl delete all --all -n fastapi-starter
```

## API Endpoints

- `POST /api/v1/logger/log_producer` - Log producer events
- `POST /api/v1/logger/log_receiver` - Log receiver events
- `GET /api/v1/logger/` - Health check

## Event Logging

The logger service receives events from:
- **EventProducer**: Logs when messages are sent to RabbitMQ queues
- **EventReceiver**: Logs when messages are received from RabbitMQ queues

Each log entry includes:
- `correlation_id`: Unique request identifier for tracing
- `queue_name`: RabbitMQ queue name
- `service_name`: Name of the service (producer or receiver)
- `task_type`: "start" or "end"
- `description`: Optional description or error message

## Structure

```
.
├── api/
│   ├── __init__.py
│   ├── logger.py          # Logging functions
│   ├── models.py          # Pydantic models (LogProducer, LogReceiver)
│   └── router.py          # FastAPI router
├── endpoint.py           # FastAPI application entry point
├── Dockerfile
├── README.md
├── logger-pod.yaml       # Kubernetes deployment
└── requirements.txt
```

## License

Licensed under the Apache License, Version 2.0.
