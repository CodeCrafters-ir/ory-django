#!/bin/bash

echo "Setting up Ory databases and running migrations..."

# Create necessary directories if they don't exist
mkdir -p scripts config/kratos

# Create Postgres init script
cat > scripts/init-multiple-postgres-dbs.sh << 'END'
#!/bin/bash

set -e
set -u

function create_database() {
  local database=$1
  echo "Creating database '$database'"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE $database;
    GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
  echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
  for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
    create_database $db
  done
  echo "Multiple databases created"
fi
END

chmod +x scripts/init-multiple-postgres-dbs.sh

# Create Kratos identity schema
cat > config/kratos/identity.schema.json << 'END'
{
  "$id": "https://schemas.ory.sh/presets/kratos/identity.schema.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Person",
  "type": "object",
  "properties": {
    "traits": {
      "type": "object",
      "properties": {
        "email": {
          "type": "string",
          "format": "email",
          "title": "E-Mail",
          "minLength": 3,
          "ory.sh/kratos": {
            "credentials": {
              "password": {
                "identifier": true
              }
            },
            "verification": {
              "via": "email"
            },
            "recovery": {
              "via": "email"
            }
          }
        },
        "name": {
          "type": "object",
          "properties": {
            "first": {
              "type": "string",
              "title": "First Name"
            },
            "last": {
              "type": "string",
              "title": "Last Name"
            }
          }
        }
      },
      "required": [
        "email"
      ],
      "additionalProperties": false
    }
  }
}
END

# Create Kratos configuration
cat > config/kratos/kratos.yml << 'END'
version: v1.0.0

dsn: postgres://ory:ory_password@ory_postgres:5432/kratos?sslmode=disable

serve:
  public:
    base_url: http://localhost:4433/
    cors:
      enabled: true
      allowed_origins:
        - http://localhost:3000
      allowed_methods:
        - POST
        - GET
        - PUT
        - PATCH
        - DELETE
      allowed_headers:
        - Authorization
        - Content-Type
      exposed_headers:
        - Content-Type
      allow_credentials: true
  admin:
    base_url: http://localhost:4434/

selfservice:
  default_browser_return_url: http://localhost:3000/
  allowed_return_urls:
    - http://localhost:3000/

  methods:
    password:
      enabled: true
    link:
      enabled: true
    code:
      enabled: true

  flows:
    settings:
      ui_url: http://localhost:3000/settings
      privileged_session_max_age: 15m
    recovery:
      enabled: true
      ui_url: http://localhost:3000/recovery
    verification:
      enabled: true
      ui_url: http://localhost:3000/verification
    login:
      ui_url: http://localhost:3000/login
      lifespan: 10m
    registration:
      ui_url: http://localhost:3000/registration
      lifespan: 10m
      after:
        password:
          hooks:
            - hook: session

log:
  level: debug
  format: text
  leak_sensitive_values: true

secrets:
  cookie:
    - PLEASE-CHANGE-ME-I-AM-VERY-INSECURE
  cipher:
    - 32-LONG-SECRET-NOT-SECURE-AT-ALL

ciphers:
  algorithm: xchacha20-poly1305

hashers:
  algorithm: argon2
  argon2:
    iterations: 1
    memory: 128MB
    parallelism: 4
    salt_length: 16
    key_length: 32

identity:
  default_schema_id: default
  schemas:
    - id: default
      url: file:///etc/config/kratos/identity.schema.json
END

echo "Configuration files created."

# Start PostgreSQL only
docker compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Run migrations directly
echo "Running Hydra migrations..."
docker run --rm \
  --network ory_network \
  -e DSN=postgres://ory:ory_password@ory_postgres:5432/hydra?sslmode=disable \
  oryd/hydra:v2.2.0 \
  migrate sql -e --yes

echo "Running Kratos migrations..."
docker run --rm \
  --network ory_network \
  -v $(pwd)/config/kratos:/etc/config/kratos \
  -e DSN=postgres://ory:ory_password@ory_postgres:5432/kratos?sslmode=disable \
  oryd/kratos:v1.0.0 \
  migrate sql -e --yes

echo "Migrations completed successfully. Now starting all services..."

# Now start all other services
docker compose up -d

echo "All services started. Waiting for them to be ready..."
sleep 10

echo "Setup complete!"
