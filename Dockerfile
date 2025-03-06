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
