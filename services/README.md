# FastAPI Starter Kit - Microservices

This directory contains microservices for the FastAPI starter kit.

## Current Services

- **dataservice** - Simple data processing service that handles data transformation via RabbitMQ

## Adding New Services

To add a new microservice:

1. Create a new folder under `services/`
2. Implement a service class with a `call()` method that accepts JSON string and returns `(response_json_string, task_type)`
3. Use `EventReceiver` from `rabbitmq_client.py` to listen to RabbitMQ queues
4. Add service configuration to `docker-compose.yml`

See `dataservice/` for a reference implementation.

## License

Licensed under the Apache License, Version 2.0.
