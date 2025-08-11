# file: Dockerfile
# This is for deploy of just stack exchange agent

# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory in the container
WORKDIR /app

# 3. Copy the requirements file and install dependencies
COPY requirements_cloudrun.txt .
RUN pip install --no-cache-dir -r requirements_cloudrun.txt

# 4. Copy your application code into the container
# This assumes your agent code is inside an 'adk_lab' directory
COPY . /app/adk_lab

# 5. Tell Cloud Run to listen on the port defined by the PORT environment variable
# The default is 8080
EXPOSE 8080

# 6. Define the command to run your application
# The ENTRYPOINT is fixed. The CMD provides a default module and can be overridden.
ENTRYPOINT ["python", "-m"]
CMD ["adk_lab.stackexchange_agent.main"]