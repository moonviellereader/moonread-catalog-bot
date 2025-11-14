FROM python:3.11-slim

WORKDIR /app

# Copy files
COPY requirements.txt .
COPY MoonCatalogBot.py .
COPY titles_and_links_alphabetical.csv .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run bot
CMD ["python", "MoonCatalogBot.py"]
