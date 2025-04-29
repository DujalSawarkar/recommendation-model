FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn


# Copy application code


# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app"]