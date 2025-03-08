#!/bin/bash

echo "Setting up Ory environment..."

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

dsn: postgres://ory:ory_password@postgres:5432/kratos?sslmode=disable

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

echo "Starting all services..."
docker compose up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Creating OAuth2 client..."
docker compose exec hydra hydra create client \
  --endpoint http://localhost:4445 \
  --grant-type authorization_code,refresh_token,client_credentials \
  --response-type code,id_token \
  --scope openid,offline \
  --redirect-uri http://localhost:3000/callback

echo "Setup complete!"
echo "UI is available at: http://localhost:3000"
echo "Kratos API: http://localhost:4433"
echo "Hydra API: http://localhost:4444"
