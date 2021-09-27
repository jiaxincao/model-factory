ARG DOCKER_REGISTRY

FROM $DOCKER_REGISTRY/model_factory_base_image


################################################################################
# Install packages.
################################################################################

RUN pip3 install croniter


################################################################################
# Copy source code
################################################################################
COPY ./core /model-factory/src/core
COPY ./services/model_factory_frontend /model-factory/src/services/model_factory_frontend
COPY ./services/model_factory_trigger_service /model-factory/src/services/model_factory_trigger_service

WORKDIR /model-factory/src


################################################################################
# Set up the startup command
################################################################################
CMD python3 -m services.model_factory_trigger_service.main run-triggers
