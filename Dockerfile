# Start with a Python version that you know works for your other packages
# Using Debian Bookworm as it has a recent sqlite3
FROM python:3.11-slim-bookworm

# Set environment variables for non-interactive apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including a compatible sqlite3
# Also install build-essential for any C extensions that might still need to compile
# and git for any pip packages that might pull from git
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    sqlite3 \
    build-essential \
    git \
    # Add cmake and pkg-config just in case some deep dependency needs them,
    # though pre-compiled wheels for Python 3.11 should minimize this.
    cmake \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements.txt first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
# When using a system sqlite3 >= 3.35.0, you might NOT need pysqlite3-binary.
# Test without it first in requirements.txt if your base image's sqlite3 is sufficient.
# If you removed pysqlite3-binary, make sure the system sqlite3 is indeed >= 3.35.0.
# The python:3.11-slim-bookworm image *should* have sqlite3 3.40.0+
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run Streamlit
# Vercel will map an external port to this internal 8501
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
