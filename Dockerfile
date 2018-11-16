# Use an official Python runtime as a parent image
FROM python:2.7-slim

RUN apt-get update && apt-get install --no-install-recommends -yq \
    python-pip

# Set the working directory
WORKDIR /auto_pr_versioning

# Copy the current directory into /app
ADD . /auto_pr_versioning

# Install all the requirements
RUN pip install -i http://pypi-staging.picwell.com/simple --trusted-host pypi-staging.picwell.com -r requirements.txt

CMD python main.py -n $GIT_REPO_NAME -t $GIT_TOKEN