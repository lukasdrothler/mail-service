FROM python:3.14-slim-bookworm

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1

# Copy requirements first for better Docker layer caching
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the source code
COPY . .

CMD ["python3", "main.py"]