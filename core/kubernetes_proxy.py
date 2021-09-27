from core.config import Config
from core import consts
from datetime import datetime
from kubernetes import client, config, utils
import os


class KubernetesProxy:
    @staticmethod
    def load_config():
        exe_environ = os.environ.get("MF_EXECUTION_ENVIRONMENT", "k8s")

        if exe_environ == 'k8s':
            config.load_incluster_config()
        elif exe_environ == 'local':
            config.load_kube_config()
        else:
            raise Exception("Unknown execution environment: {}".format(exe_environ))

    @staticmethod
    def create_job(
        job_id,
        docker_image,
        cpu_request,
        memory_request,
        storage_request,
        ttl_after_finished,
        command=None,
        gpu_request=None,
        pool=consts.DEFAULT_POOL,
        active_deadline_seconds=None,
    ):
        if gpu_request:
            resource_requirements = client.V1ResourceRequirements(
                requests={
                    "cpu": cpu_request,
                    "memory": memory_request,
                    "nvidia.com/gpu": gpu_request,
                },
                limits={
                    "cpu": cpu_request,
                    "memory": memory_request,
                    "nvidia.com/gpu": gpu_request,
                },
            )
        else:
            resource_requirements = client.V1ResourceRequirements(
                requests={
                    "cpu": cpu_request,
                    "memory": memory_request,
                },
                limits={
                    "cpu": cpu_request,
                    "memory": memory_request,
                },
            )

        # Create k8s job object.
        container = client.V1Container(
            name=job_id,
            image=docker_image,
            volume_mounts=[
                client.V1VolumeMount(
                    name="model-factory-pipelines-volume",
                    mount_path="/model-factory/execution",
                )
            ],
            resources=resource_requirements,
            command=command,
            security_context=client.V1SecurityContext(
                allow_privilege_escalation=True,
                privileged=True,
            ),
            image_pull_policy="Always",
        )

        volume = client.V1Volume(
            name="model-factory-pipelines-volume",
            ephemeral=client.V1EphemeralVolumeSource(
                volume_claim_template=client.V1PersistentVolumeClaimTemplate(
                    spec=client.V1PersistentVolumeClaimSpec(
                        access_modes=["ReadWriteOnce"],
                        resources=client.V1ResourceRequirements(
                            requests={
                                "storage": storage_request,
                            }
                        ),
                        storage_class_name=Config.STORAGE_CLASS,
                    ),
                )
            ),
        )

        node_selector = {
            "model-factory-pool": pool
        } if pool != consts.DEFAULT_POOL else None

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={
                    "job_id": job_id,
                }
            ),
            spec=client.V1PodSpec(
                containers=[container],
                volumes=[volume],
                restart_policy="Never",
                node_selector=node_selector,
            ),
        )

        spec = client.V1JobSpec(
            template=template,
            backoff_limit=0,
            ttl_seconds_after_finished=ttl_after_finished,
            active_deadline_seconds=active_deadline_seconds,
        )

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_id,
            ),
            spec=spec
        )

        # Create k8s client.
        KubernetesProxy.load_config()
        k8s_batch_api = client.BatchV1Api()

        # Create k8s job.
        k8s_batch_api.create_namespaced_job(
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
            body=job,
        )

    @staticmethod
    def list_jobs():
        KubernetesProxy.load_config()
        k8s_batch_api = client.BatchV1Api()

        return k8s_batch_api.list_namespaced_job(
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
        )

    @staticmethod
    def delete_job(job_id):
        KubernetesProxy.load_config()
        k8s_batch_api = client.BatchV1Api()

        return k8s_batch_api.delete_namespaced_job(
            name=job_id,
            body=client.V1DeleteOptions(
                propagation_policy="Background",
            ),
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
        )

    @staticmethod
    def delete_pod(pod_id):
        KubernetesProxy.load_config()
        k8s_core_api = client.CoreV1Api()

        return k8s_core_api.delete_namespaced_pod(
            name=pod_id,
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
        )

    @staticmethod
    def get_job_log(pod_name):
        KubernetesProxy.load_config()

        api_instance = client.CoreV1Api()
        api_response = api_instance.read_namespaced_pod_log(
            name=pod_name,
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
        )
        return api_response

    @staticmethod
    def get_job(job_name):
        KubernetesProxy.load_config()

        k8s_batch_api = client.BatchV1Api()
        api_response = k8s_batch_api.list_namespaced_job(
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
            label_selector='job-name={}'.format(job_name),
        )
        return api_response.items[0]

    @staticmethod
    def get_pod(job_id):
        KubernetesProxy.load_config()

        k8s_batch_api = client.CoreV1Api()
        api_response = k8s_batch_api.list_namespaced_pod(
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
            label_selector='job-name={}'.format(job_id),
        )
        return api_response.items and api_response.items[0]

    @staticmethod
    def list_pods():
        """
        get k8s active pods info
        """
        KubernetesProxy.load_config()

        k8s_core_api = client.CoreV1Api()
        api_response = k8s_core_api.list_namespaced_pod(
            namespace=consts.MODEL_FACTORY_PIPELINES_NAMESPACE,
        )
        return api_response

    @staticmethod
    def restart_deployment(namespace, deployment):
        KubernetesProxy.load_config()
        v1_apps = client.AppsV1Api()

        now = str(datetime.utcnow().isoformat("T") + "Z")
        body = {
            'spec': {
                'template':{
                    'metadata': {
                        'annotations': {
                            'kubectl.kubernetes.io/restartedAt': now
                        }
                    }
                }
            }
        }
        return v1_apps.patch_namespaced_deployment(deployment, namespace, body, pretty='true')
