ARG DOCKER_REGISTRY

FROM $DOCKER_REGISTRY/model_factory_base_image


################################################################################
# Install packages needed by model factory frontend.
################################################################################

RUN apt update
RUN apt install python3 python3-pip tree vim git npm -y

RUN pip3 install pymongo click tabulate docker dataclasses python-dateutil google-auth oauthlib pyyaml requests_oauthlib jsonpickle gitpython flask flask_wtf pytz wtforms


################################################################################
# Copy source code
################################################################################
COPY ./services/model_factory_dashboard /model-factory/src/services/model_factory_dashboard
WORKDIR /model-factory/src/services/model_factory_dashboard

RUN npm install


################################################################################
# Set up the startup command
################################################################################
CMD npm run serve
