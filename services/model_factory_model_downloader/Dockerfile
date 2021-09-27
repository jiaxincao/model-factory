ARG DOCKER_REGISTRY

FROM $DOCKER_REGISTRY/model_factory_base_image


################################################################################
# Copy source code
################################################################################
COPY ./core /model-factory/src/core
COPY ./services/model_factory_model_downloader /model-factory/src/services/model_factory_model_downloader

WORKDIR /model-factory/src
