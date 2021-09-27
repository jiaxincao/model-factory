################################################################################
# Section 1: Parent Image
################################################################################
ARG DOCKER_REGISTRY
FROM "$DOCKER_REGISTRY/model_factory_base_image"


################################################################################
# Section 2: Pipeline Custom Package Installation
################################################################################

# If you need any packages or special setup for your pipeline, please put them in section 2.
RUN pip3 install torch torchvision


################################################################################
# Section 3: Set up environment variables
################################################################################
RUN echo "export PYTHONPATH='/model-factory/src'" >> /root/.bashrc
ENV PYTHONPATH='/model-factory/src'
