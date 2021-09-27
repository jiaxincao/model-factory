from core import utils
from core.config import Config
from core.parameter import Parameter, ParameterGroup
import importlib
import os


class PipelineManager:
    pipelines = {}
    operators = {}

    @classmethod
    def init(cls):
        pipelines_dir = os.path.join(utils.get_model_factory_basedir(), "pipelines")

        if os.path.exists(pipelines_dir):
            for pipeline_dir in os.listdir(pipelines_dir):
                pipeline_init_file = os.path.join(
                    utils.get_model_factory_basedir(),
                    "pipelines",
                    pipeline_dir,
                    "__init__.py",
                )

                if not os.path.isfile(pipeline_init_file):
                    continue

                module = importlib.import_module("pipelines.{}".format(pipeline_dir))

                pipeline = getattr(module, "PIPELINE", None)
                if pipeline:
                    cls.pipelines[pipeline.name] = pipeline

                operators = getattr(module, "OPERATORS", [])
                for operator in operators:
                    cls.operators[operator.operator_id] = operator

        cls.initialized = True

    @classmethod
    def try_get_pipeline(cls, name):
        return cls.pipelines.get(name, None)

    @classmethod
    def get_pipeline(cls, name):
        assert name in cls.pipelines, "Cannot find model factory pipeline \"{}\"!".format(name)
        return cls.pipelines[name]

    @classmethod
    def get_all_pipelines(cls):
        return list(cls.pipelines.values())

    @classmethod
    def get_operator_by_id(cls, operator_id):
        assert operator_id in cls.operators, "Cannot find operator \"{}\"!".format(operator_id)
        return cls.operators[operator_id]

    @classmethod
    def get_operator_cmd(cls, job_id, operator_id, operator_params, cpu, execution_mode):
        return (
            "python3 -m core.operator_executor execute-operator {} {} --cpu {} --operator-params '{}' --execution-mode '{}'"
        ).format(job_id, operator_id, cpu, operator_params, execution_mode)

    @classmethod
    def create_operator_params(cls, operator_input_schema, operator_params):
        params = {}

        # Fill in params from the pipeline params schema default values.
        mandatory_fields = set()
        def fill_params_based_on_schema(param_node, operator_input_schema, key_path):
            for param in operator_input_schema:
                if isinstance(param, Parameter):
                    param_node[param.name] = param.default

                    if param.mandatory:
                        mandatory_fields.add(".".join(key_path + [param.name]))
                elif isinstance(param, ParameterGroup):
                    sub_params = {}
                    param_node[param.name] = sub_params
                    fill_params_based_on_schema(sub_params, param.parameters, key_path + [param.name])

        fill_params_based_on_schema(params, operator_input_schema, [])

        # Fill in the parmas with the pass in operator_params.
        filled_fields = set()
        def fill_params_based_on_input(param_node, input_param_node, key_path):
            for k, v in input_param_node.items():
                assert k in param_node, (
                    "Operator input does not take config for key path \"{}\"! "
                ).format(".".join(key_path + [k]))

                if not isinstance(v, dict):
                    param_node[k] = v
                    filled_fields.add(".".join(key_path + [k]))
                else:
                    assert isinstance(param_node[k], dict)
                    fill_params_based_on_input(param_node[k], v, key_path + [k])

        fill_params_based_on_input(params, operator_params, [])

        # Make sure all mandatory fields are filled.
        missing_fields = mandatory_fields - filled_fields
        assert not missing_fields, "The following mandatory json input keys are missing: \n{}".format(
            "\n".join(["* {}".format(field) for field in sorted(missing_fields)])
        )

        return params


PipelineManager.init()
