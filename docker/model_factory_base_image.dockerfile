FROM nvidia/cuda:11.1-base-ubuntu20.04


# Define variables.
ARG MF_FRONTEND_ENDPOINT

ARG MONGO_DB_ENDPOINT

ARG DOCKER_REGISTRY

ARG S3_ENDPOINT
ARG S3_BUCKET=model-factory
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

ARG STORAGE_CLASS


# Install packages.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update
RUN apt install python3 python3-pip tree wget git vim net-tools iputils-ping docker.io nfs-common openssh-server htop -y
RUN pip3 install boto3 click dataclasses docker git+https://github.com/kubernetes-client/python.git@master gitpython jsonpickle pudb pymongo python-dateutil pytz pyyaml tabulate thrift treelib croniter

# create a model factory alias
RUN echo 'export MODEL_FACTORY_PATH=/model-factory/src' >> ~/.bashrc
RUN echo 'export PYTHONPATH=/model-factory/src' >> ~/.bashrc
RUN echo 'alias mf="PYTHONPATH=/model-factory/src python3 -m cli.mf"' >> ~/.bashrc
RUN echo "PS1='\\[\\e]0;\\w\\a\\]\\[\\e[32m\\]\\u@\\h:\\w$\\[\\e[0m\\] '" >> ~/.bashrc

# Set up model factory config.
RUN echo "[default]\n\
mf_frontend_endpoint=$MF_FRONTEND_ENDPOINT\n\
mongo_db_endpoint=$MONGO_DB_ENDPOINT\n\
s3_endpoint=$S3_ENDPOINT\n\
s3_bucket=$S3_BUCKET\n\
docker_registry=$DOCKER_REGISTRY\n\
aws_access_key_id=$AWS_ACCESS_KEY_ID\n\
aws_secret_access_key=$AWS_SECRET_ACCESS_KEY\n\
storage_class=$STORAGE_CLASS\n\
" > /root/.model_factory.ini

# Prepare execution directory.
RUN mkdir -p /model-factory/execution
WORKDIR /model-factory/execution
