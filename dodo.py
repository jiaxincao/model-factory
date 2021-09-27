from core.config import Config


def task_create_k8s_namespaces():
    return {
        "actions": [
            "kubectl create namespace model-factory-pipelines --dry-run=client -o yaml | kubectl apply -f -",
            "kubectl create namespace model-factory-services --dry-run=client -o yaml | kubectl apply -f -",
        ]
    }


def task_model_factory_frontend():
    return {
        "actions": [
            "docker pull {}/model_factory_base_image".format(Config.DOCKER_REGISTRY),
            "docker build --build-arg DOCKER_REGISTRY={} . -f services/model_factory_frontend/Dockerfile -t {}/model-factory-frontend".format(
                Config.DOCKER_REGISTRY, Config.DOCKER_REGISTRY
            ),
            "docker push {}/model-factory-frontend".format(Config.DOCKER_REGISTRY),
            "DOCKER_REGISTRY={} envsubst < services/model_factory_frontend/deployment/deployment.yaml | kubectl apply -f -".format(Config.DOCKER_REGISTRY),
        ],
    }


def task_model_factory_dashboard():
    return {
        "actions": [
            "docker pull {}/model_factory_base_image".format(Config.DOCKER_REGISTRY),
            "docker build --build-arg DOCKER_REGISTRY={} . -f services/model_factory_dashboard/Dockerfile -t {}/model-factory-dashboard".format(
                Config.DOCKER_REGISTRY, Config.DOCKER_REGISTRY
            ),
            "docker push {}/model-factory-dashboard".format(Config.DOCKER_REGISTRY),
            "DOCKER_REGISTRY={} envsubst < services/model_factory_dashboard/deployment/deployment.yaml | kubectl apply -f -".format(Config.DOCKER_REGISTRY),
        ],
    }


def task_model_factory_execution_syncer():
    return {
        "actions": [
            "docker pull {}/model_factory_base_image".format(Config.DOCKER_REGISTRY),
            "docker build --build-arg DOCKER_REGISTRY={} . -f services/model_factory_execution_syncer/Dockerfile -t {}/model-factory-execution-syncer".format(
                Config.DOCKER_REGISTRY, Config.DOCKER_REGISTRY
            ),
            "docker push {}/model-factory-execution-syncer".format(Config.DOCKER_REGISTRY),
            "DOCKER_REGISTRY={} envsubst < services/model_factory_execution_syncer/deployment/deployment.yaml | kubectl apply -f -".format(Config.DOCKER_REGISTRY),
        ],
    }


def task_model_factory_autohide_service():
    return {
        "actions": [
            "docker pull {}/model_factory_base_image".format(Config.DOCKER_REGISTRY),
            "docker build --build-arg DOCKER_REGISTRY={} . -f services/model_factory_autohide_service/Dockerfile -t {}/model-factory-autohide-service".format(
                Config.DOCKER_REGISTRY, Config.DOCKER_REGISTRY
            ),
            "docker push {}/model-factory-autohide-service".format(Config.DOCKER_REGISTRY),
            "DOCKER_REGISTRY={} envsubst < services/model_factory_autohide_service/deployment/deployment.yaml | kubectl apply -f -".format(Config.DOCKER_REGISTRY),
        ],
    }


def task_model_factory_trigger_service():
    return {
        "actions": [
            "docker pull {}/model_factory_base_image".format(Config.DOCKER_REGISTRY),
            "docker build --build-arg DOCKER_REGISTRY={} . -f services/model_factory_trigger_service/Dockerfile -t {}/model-factory-trigger-service".format(
                Config.DOCKER_REGISTRY, Config.DOCKER_REGISTRY
            ),
            "docker push {}/model-factory-trigger-service".format(Config.DOCKER_REGISTRY),
            "DOCKER_REGISTRY={} envsubst < services/model_factory_trigger_service/deployment/deployment.yaml | kubectl apply -f -".format(Config.DOCKER_REGISTRY),
        ],
    }


def task_model_factory_model_downloader():
    return {
        "actions": [
            "docker pull {}/model_factory_base_image".format(Config.DOCKER_REGISTRY),
            "docker build --build-arg DOCKER_REGISTRY={} . -f services/model_factory_model_downloader/Dockerfile -t {}/model-factory-model-downloader".format(
                Config.DOCKER_REGISTRY, Config.DOCKER_REGISTRY
            ),
            "docker push {}/model-factory-model-downloader".format(Config.DOCKER_REGISTRY),
        ],
    }


def task_server():
    return {
        "actions": None,
        "task_dep": [
            "create_k8s_namespaces",
            "model_factory_frontend",
            "model_factory_frontend",
            "model_factory_execution_syncer",
            "model_factory_autohide_service",
            "model_factory_trigger_service",
            "model_factory_model_downloader",
        ],
    }


def task_client():
    return {
        "actions": [
            "echo \033[93mSetting up model factory client on your devbox...\033[0m",
            "pip3 install awscli boto3 click dataclasses docker git+https://github.com/kubernetes-client/python.git@release-19.0 gitpython jsonpickle pudb pymongo python-dateutil pytz pyyaml tabulate thrift treelib ansible_runner croniter slackclient",
            "PYTHONPATH=`pwd` python3 cli/mf.py dev install-alias",
            "echo \033[92mModel factory has been successully installed. Please restart your shell before using model factory!\033[0m",
        ]
    }


def task_build_base_image():
    return {
        "actions": [
            (
                "docker build . -f docker/model_factory_base_image.dockerfile "
                "--build-arg MONGO_DB_ENDPOINT={} "
                "--build-arg MF_FRONTEND_ENDPOINT={} "
                "--build-arg S3_ENDPOINT={} "
                "--build-arg S3_BUCKET={} "
                "--build-arg DOCKER_REGISTRY={} "
                "--build-arg AWS_ACCESS_KEY_ID={} "
                "--build-arg AWS_SECRET_ACCESS_KEY={} "
                "--build-arg STORAGE_CLASS={} "
                "-t {}/model_factory_base_image"
            ).format(
                Config.MONGO_DB_ENDPOINT,
                Config.MF_FRONTEND_ENDPOINT,
                Config.S3_ENDPOINT,
                Config.S3_BUCKET,
                Config.DOCKER_REGISTRY,
                Config.AWS_ACCESS_KEY_ID,
                Config.AWS_SECRET_ACCESS_KEY,
                Config.STORAGE_CLASS,
                Config.DOCKER_REGISTRY,
            ),
            "docker push {}/model_factory_base_image".format(
                Config.DOCKER_REGISTRY,
            ),
        ]
    }
