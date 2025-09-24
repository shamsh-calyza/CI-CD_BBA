# Use a lightweight Python base image
FROM python:3.12-slim

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxrandr2 \
    libatk1.0-0 \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN curl -SL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
    && apt install -y ./chrome.deb \
    && rm chrome.deb

# Install Chromedriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) \
    && DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION) \
    && wget https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Set environment variable for SQS queue
ENV RESULT_QUEUE_URL=https://sqs.us-east-2.amazonaws.com/705707996353/ResultQueue

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Lambda function code
COPY lambda_function.py .

# Set the default command to run your script
CMD ["python", "lambda_function.py"]
