ARG DOCKER_REGISTRY

FROM $DOCKER_REGISTRY/model_factory_base_image


################################################################################
# Install packages needed by model factory frontend.
################################################################################

RUN apt update
RUN apt install python3 python3-pip tree vim git -y

RUN pip3 install pymongo click tabulate docker dataclasses python-dateutil google-auth oauthlib pyyaml requests_oauthlib jsonpickle boto3 git+https://github.com/kubernetes-client/python.git@master gitpython flask flask-cors


################################################################################
# Copy source code
################################################################################
COPY ./core /model-factory/src/core
COPY ./services/model_factory_frontend /model-factory/src/services/model_factory_frontend

WORKDIR /model-factory/src


################################################################################
# Set up the startup command
################################################################################
CMD python3 -m services.model_factory_frontend.server
