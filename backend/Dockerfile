FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install bird CLI for Twitter/X cookie-based data access
# Pinned to 0.8.0 — upstream @steipete/bird is deprecated, repo may be deleted
RUN npm install -g @steipete/bird@0.8.0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static/avatars

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
