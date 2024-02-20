# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at the working directory
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 4002 available to the world outside this container
EXPOSE 4002

# Define environment variable
ENV PORT=4002
ENV AMQP_URL='amqp://guest:guest@redditmqmg.a2gkhna2h0crepaw.eastus.azurecontainer.io:5672/'

# Run app.py when the container launches
CMD ["python", "app.py"]
