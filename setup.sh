# Create directories for email templates (to suppress warnings)
mkdir -p kratos/courier-templates/recovery/valid
mkdir -p kratos/courier-templates/verification/valid

# Create dummy email templates
cat > kratos/courier-templates/recovery/valid/email.body.plaintext.gotmpl << EOF
Recovery link: {{ .RecoveryURL }}
EOF

cat > kratos/courier-templates/verification/valid/email.body.plaintext.gotmpl << EOF
Verification link: {{ .VerificationURL }}
EOF#!/bin/bash
# Setup script for Ory integration

set -e  # Exit on any error

# Create necessary directories
mkdir -p kratos

# Create Kratos configuration file
cat > kratos/kratos.yml << EOF
version: v0.11.0

dsn: postgres://kratos:secret@kratos-db:5432/kratos?sslmode=disable

serve:
  public:
    base_url: http://localhost:4433/
  admin:
    base_url: http://localhost:4434/

selfservice:
  default_browser_return_url: http://localhost:4455/

  methods:
    password:
      enabled: true

  flows:
    login:
      ui_url: http://localhost:4455/login
    registration:
      ui_url: http://localhost:4455/registration
    verification:
      enabled: false
    recovery:
      enabled: false

log:
  level: debug

# Courier configuration is provided via environment variables

secrets:
  cookie:
    - PLEASE-CHANGE-ME-I-AM-VERY-INSECURE

identity:
  default_schema_id: default
  schemas:
    - id: default
      url: file:///etc/config/kratos/identity.schema.json
EOF

# Create identity schema for Kratos
cat > kratos/identity.schema.json << EOF
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
              "type": "string"
            },
            "last": {
              "type": "string"
            }
          }
        }
      },
      "required": [
        "email"
      ],
      "additionalProperties": true
    }
  }
}
EOF

# Create Dockerfile
cat > Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make setup script executable
RUN chmod +x /app/setup.sh

CMD ["/app/setup.sh"]
EOF

# Create requirements.txt
cat > requirements.txt << EOF
requests==2.31.0
EOF

# Wait for services to be ready
echo "Waiting for Ory services to start..."
sleep 15

# Make the main script executable
chmod +x main.py

# Run the main script
echo "Running the Ory integration example..."
python main.py