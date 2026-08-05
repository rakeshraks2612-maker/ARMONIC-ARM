FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Install package
RUN pip install -e .

# Default: run with example config (cProfile fallback if APX unavailable)
CMD ["python", "-m", "armonic.run", "--config", "config.example.yaml"]
