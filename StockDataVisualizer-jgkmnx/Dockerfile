# Official python image as base image
FROM python:3.8-slim-buster

# set working directory in container to /app
WORKDIR /app

# copy contents of current directory in container to /app directory 
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# install any needed packages 
RUN pip install --no-cache-dir -r requirements.txt 

# set default commands to run when starting the container 
CMD ["python", "app.py"]