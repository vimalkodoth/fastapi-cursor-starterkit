# FastAPI Starter Kit - Data Service

Data processing microservice that handles data transformation via RabbitMQ. It listens to the `data_queue` and processes incoming data requests.

**Features:**
- Listens to RabbitMQ queue for data processing requests
- Supports multiple data types (string, number, list, dict)
- Simple data transformation based on description hints
- Returns processed data via RabbitMQ RPC pattern

## Instructions

To run all services, check instructions in main [README](../../README.md)

#### Run the service without Docker

1. Install libraries

```
pip install -r requirements.txt
```

2. Start service

```
python main.py
```

#### Build and run individual container

1. Build container

```
docker build --tag data-service .
```

2. Run container

```
docker run -it -d --name data-service \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_PORT=5672 \
  -e RABBITMQ_USER=guest \
  -e RABBITMQ_PASSWORD=welcome1 \
  -e QUEUE_NAME=data_queue \
  -e SERVICE_NAME=data \
  data-service:latest
```

## Data Processing

The service processes different data types based on the `description` field:

**String Processing:**
- `"uppercase"` - Converts to uppercase
- `"reverse"` - Reverses the string
- Default - Adds "Processed: " prefix

**Number Processing:**
- `"square"` - Squares the number
- `"double"` - Doubles the number
- Default - Returns as-is

**List Processing:**
- `"reverse"` - Reverses the list
- `"sort"` - Sorts the list
- Default - Returns with metadata (count, items)

**Dictionary Processing:**
- Adds metadata (processed flag, keys count)

## Environment Variables

- `RABBITMQ_HOST` - RabbitMQ host (default: `rabbitmq`)
- `RABBITMQ_PORT` - RabbitMQ port (default: `5672`)
- `RABBITMQ_USER` - RabbitMQ username (default: `guest`)
- `RABBITMQ_PASSWORD` - RabbitMQ password (default: `welcome1`)
- `QUEUE_NAME` - Queue name to listen to (default: `data_queue`)
- `SERVICE_NAME` - Service name (default: `data`)
## Structure

```
.
├── app/
│   ├── __init__.py
│   └── data_service.py    # Data processing logic
├── main.py                 # Service entry point
├── rabbitmq_client.py      # RabbitMQ EventReceiver (kombu)
├── Dockerfile
├── README.MD
└── requirements.txt
```

## License

Licensed under the Apache License, Version 2.0.
