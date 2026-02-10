#!/usr/bin/env bash

set -e
(
count=0;
# Execute list_users until service is up and running
until timeout 5 rabbitmqctl list_users >/dev/null 2>/dev/null || (( count++ >= 60 )); do sleep 1; done;

# Register user and ensure permissions (needed for RPC callback queues e.g. amq.gen-*)
if rabbitmqctl list_users | grep $RABBITMQ_USER > /dev/null
then
  echo "User '$RABBITMQ_USER' already exists, ensuring permissions..."
else
  echo "Creating user '$RABBITMQ_USER'..."
  rabbitmqctl add_user $RABBITMQ_USER $RABBITMQ_PASSWORD
  echo "User '$RABBITMQ_USER' creation completed"
fi
rabbitmqctl set_user_tags $RABBITMQ_USER administrator
rabbitmqctl set_permissions -p / $RABBITMQ_USER ".*" ".*" ".*"
echo "Permissions set for '$RABBITMQ_USER'"
) &

# Call original entrypoint
exec docker-entrypoint.sh rabbitmq-server $@
