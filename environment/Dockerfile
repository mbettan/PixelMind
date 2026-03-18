FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements or pyproject.toml
COPY pyproject.toml .
COPY .env* .

# Install dependencies
RUN pip install --no-cache-dir .

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy source code
COPY src/ ./src/

# Command to run the application
ENTRYPOINT ["python", "src/main.py"]
