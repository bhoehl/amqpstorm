#!/bin/bash
set -o pipefail
set -e

# Git Bash/MSYS maps "/" to a Windows path; RabbitMQ's default vhost must stay "/".
export MSYS_NO_PATHCONV=1

# Build RabbitMQ container and start it.
docker rm amqpstormdev -f || true
docker build -t amqpstormdev ./docker/
docker run -d --hostname rmq.eandersson.net --name amqpstormdev -p 5671:5671 -p 5672:5672 -p 15671:15671 -p 15672:15672 amqpstormdev
docker cp amqpstormdev:/etc/rabbitmq/ssl/ ./amqpstorm/tests/resources/

# Wait for RabbitMQ to startup properly.
docker exec amqpstormdev wait-for-rabbitmq

# Print RabbitMQ version
echo "RabbitMQ Version: $(docker exec amqpstormdev rabbitmqctl --version)"

# Add user.
docker exec amqpstormdev rabbitmqctl add_user 'amqpstorm' '2a55f70a841f18b'
docker exec amqpstormdev rabbitmqctl -p / set_permissions 'amqpstorm' '.*' '.*' '.*'
docker exec amqpstormdev rabbitmqctl set_user_tags amqpstorm administrator

# Confirm all ports are reachable (nc on Linux CI; Python fallback for Git Bash on Windows).
check_port() {
  local host=$1 port=$2
  if command -v nc >/dev/null 2>&1; then
    nc -zv "$host" "$port"
  else
    python -c "import socket; s=socket.create_connection(('$host', $port), timeout=10); s.close(); print('Connected to $host:$port')"
  fi
}
check_port rmq.eandersson.net 5671  || exit 1
check_port rmq.eandersson.net 5672  || exit 1
check_port rmq.eandersson.net 15671 || exit 1
check_port rmq.eandersson.net 15672 || exit 1

# Wait for a few seconds to make sure RabbitMQ has time so start properly.
sleep 3

# Match .github/workflows/testing.yml dependency install.
python -m pip install -r requirements.txt -r test-requirements.txt

# Run tests.
pytest --cov=./amqpstorm --durations=5
flake8 --ignore=F821 amqpstorm/
