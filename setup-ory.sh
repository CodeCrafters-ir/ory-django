#!/bin/bash

echo "Setting up Ory Hydra and Kratos..."

# Create necessary directories
mkdir -p scripts config/kratos

# Create PostgreSQL init script
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
  admin:
    base_url: http://localhost:4434/

selfservice:
  default_browser_return_url: http://localhost:3000/
  allowed_return_urls:
    - http://localhost:3000/

  methods:
    password:
      enabled: true

  flows:
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

secrets:
  cookie:
    - PLEASE-CHANGE-ME-I-AM-VERY-INSECURE
  cipher:
    - 32-LONG-SECRET-NOT-SECURE-AT-ALL

identity:
  default_schema_id: default
  schemas:
    - id: default
      url: file:///etc/config/kratos/identity.schema.json
END

# Create Docker Compose file
cat > docker-compose.yml << 'END'
version: '3.7'

services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=ory
      - POSTGRES_PASSWORD=ory_password
      - POSTGRES_DB=ory
      - POSTGRES_MULTIPLE_DATABASES=hydra,kratos
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-multiple-postgres-dbs.sh:/docker-entrypoint-initdb.d/init-multiple-postgres-dbs.sh
    networks:
      - ory_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ory"]
      interval: 10s
      timeout: 5s
      retries: 5

  hydra-migrate:
    image: oryd/hydra:v2.2.0
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DSN=postgres://ory:ory_password@postgres:5432/hydra?sslmode=disable
    command: migrate sql -e --yes
    networks:
      - ory_network
    restart: on-failure

  hydra:
    image: oryd/hydra:v2.2.0
    depends_on:
      hydra-migrate:
        condition: service_completed_successfully
    ports:
      - "4444:4444" # Public API
      - "4445:4445" # Admin API
    environment:
      - DSN=postgres://ory:ory_password@postgres:5432/hydra?sslmode=disable
      - SERVE_PUBLIC_PORT=4444
      - SERVE_ADMIN_PORT=4445
      - URLS_SELF_ISSUER=http://localhost:4444/
      - URLS_CONSENT=http://localhost:3000/consent
      - URLS_LOGIN=http://localhost:3000/login
      - SECRETS_SYSTEM=youReallyNeedToChangeThis
      - OIDC_SUBJECT_IDENTIFIERS_SUPPORTED_TYPES=public,pairwise
      - OIDC_SUBJECT_IDENTIFIERS_PAIRWISE_SALT=youReallyNeedToChangeThis
      - LOG_LEVEL=debug
    networks:
      - ory_network
    restart: unless-stopped
    command: serve all --dev

  kratos-migrate:
    image: oryd/kratos:v1.0.0
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DSN=postgres://ory:ory_password@postgres:5432/kratos?sslmode=disable
    volumes:
      - ./config/kratos:/etc/config/kratos
    command: migrate sql -e --yes
    networks:
      - ory_network
    restart: on-failure

  kratos:
    image: oryd/kratos:v1.0.0
    depends_on:
      kratos-migrate:
        condition: service_completed_successfully
    ports:
      - "4433:4433" # Public API
      - "4434:4434" # Admin API
    environment:
      - DSN=postgres://ory:ory_password@postgres:5432/kratos?sslmode=disable
      - LOG_LEVEL=debug
    volumes:
      - ./config/kratos:/etc/config/kratos
    networks:
      - ory_network
    restart: unless-stopped
    command: serve -c /etc/config/kratos/kratos.yml --dev

networks:
  ory_network:
    external: true

volumes:
  postgres-data:
END

# Start the services
echo "Starting services..."
docker compose up -d

echo "Waiting for services to be ready..."
sleep 15

echo "Creating a test user..."
docker exec -it $(docker ps -qf "name=kratos") kratos identities import -r < <(cat << 'EOF'
{
  "identity": {
    "schema_id": "default",
    "traits": {
      "email": "test@example.com",
      "name": {
        "first": "Test",
        "last": "User"
      }
    }
  },
  "password": "password123"
}
EOF
)

echo "Creating OAuth2 client..."
docker exec -it $(docker ps -qf "name=hydra") hydra clients create \
    --endpoint http://localhost:4445 \
    --id test-client \
    --secret test-secret \
    --grant-type authorization_code,refresh_token,client_credentials \
    --response-type code,id_token \
    --scope openid,offline \
    --redirect-uri http://localhost:3000/callback

echo "Setup complete!"
echo "User credentials:"
echo "  Email: test@example.com"
echo "  Password: password123"
echo ""
echo "Client credentials:"
echo "  Client ID: test-client"
echo "  Client Secret: test-secret"
echo ""
echo "APIs are available at:"
echo "  Kratos Public API: http://localhost:4433"
echo "  Kratos Admin API: http://localhost:4434"
echo "  Hydra Public API: http://localhost:4444"
echo "  Hydra Admin API: http://localhost:4445"
