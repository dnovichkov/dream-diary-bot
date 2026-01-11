FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Copy Alembic configuration and migrations
COPY alembic.ini .
COPY migrations/ ./migrations/

# Run the bot
CMD ["python", "-m", "src.main"]
