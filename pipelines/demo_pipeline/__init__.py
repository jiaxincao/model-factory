from core.operator import Operator
from core.parameter import Parameter, ParameterGroup
from core.pipeline import Pipeline


PIPELINE = Pipeline(
    name = "demo_pipeline",
    docker_base_image = "demo_pipeline_base_image",
    main_operator_id = "pipelines.demo_pipeline.main.main",
)

OPERATORS = [
    Operator(
        operator_id="pipelines.demo_pipeline.main.main",
        input_schema=[
            Parameter(name="namespace", default="demo", help_msg="The namespace for the demo pipeline artifacts."),
        ],
        cpu_request=1,
        memory_request="1G",
        storage_request="1G",
    ),
]
