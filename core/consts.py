################################################################################
# Model Factory Config File Path.
################################################################################
MODEL_FACTORY_CONFIG_FILE = "~/.model_factory.ini"


################################################################################
# Model Factory Resource Related Consts.
################################################################################
MODEL_FACTORY_PIPELINES_NAMESPACE = "model-factory-pipelines"
MODEL_FACTORY_MODELS_NAMESPACE = "model-factory-models"

MODEL_FACTORY_DB_NAME = "model-factory"
MODEL_FACTORY_JOB_COLLECTION_NAME = "jobs"
MODEL_FACTORY_TRIGGERS_COLLECTION_NAME = "triggers"
MODEL_FACTORY_MODEL_REGISTRY = "models"
MODEL_FACTORY_PROD_MODEL = "production_models"


################################################################################
# Model Factory Core Library Consts.
################################################################################
EXECUTION_MODE_K8S = "k8s"
EXECUTION_MODE_LOCAL = "local"
EXECUTION_MODE_INPLACE = "inplace"

DEFAULT_CPU_REQUEST = 1
DEFAULT_MEMORY_REQUEST = "1G"
DEFAULT_STORAGE_REQUEST = "1G"
DEFAULT_GPU_REQUEST = 0

DEFAULT_POOL = "any"

TRIGGER_FAILURE_LIMIT = 15
