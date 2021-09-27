from core import utils as core_utils
from core.pipeline_manager import PipelineManager
import os
import stat
import tempfile


def generate_pipeline_dockerfile(pipeline_name):
    pipeline = PipelineManager.get_pipeline(pipeline_name)

    # Read dockerfile template
    docker_file_path = os.path.join(
        core_utils.get_model_factory_basedir(),
        "docker",
        "{}.dockerfile".format(pipeline.docker_base_image),
    )
    with open(docker_file_path) as fp:
        dockerfile_content = (
            "{}\n"
            "RUN mkdir -p /model-factory/execution\n"
            "COPY services/model_factory_frontend /model-factory/src/services/model_factory_frontend\n"
            "COPY core /model-factory/src/core\n"
            "COPY lib /model-factory/src/lib\n"
            "COPY pipelines/{} /model-factory/src/pipelines/{}\n"
        ).format(
            fp.read(),
            pipeline.name,
            pipeline.name,
        )

        for dependent_pipeline in pipeline.dependent_pipelines or []:
            dockerfile_content += "COPY pipelines/{} /model-factory/src/pipelines/{}\n".format(
                dependent_pipeline,
                dependent_pipeline,
            )

    # Generate dockerfile.
    os.makedirs("/tmp/model-factory", exist_ok=True)

    fp, tmp_docker_file_path = tempfile.mkstemp(
        prefix="model_factory_dockerfile_",
        dir="/tmp/model-factory",
    )
    os.write(fp, dockerfile_content.encode())
    os.close(fp)

    return tmp_docker_file_path
