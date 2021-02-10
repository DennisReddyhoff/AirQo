# Inherit from the Python Docker image
FROM python:3.7-slim
# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
# Install the Flask package via pip
RUN pip install -r requirements.txt

# Set "python" as the entry point
# Set environment variables
ENV FLASK_APP=api.py

# Expose the application's port, default is 5000 for python flask
EXPOSE 4000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=4000"]
