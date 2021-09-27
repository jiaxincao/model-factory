The installation of model factory needs to happen on both server side and client side. Model factory services will be running on the server side, while the client side will submits jobs to the services.

Model factory uses [doit](https://pydoit.org/) to manage its projects. Please do ```pip3 install doit``` before any of the following steps.


# Server

## Step 0: Prerequisite
There are a few prerequisites to use model factory:
* **A kubernetes cluster**: To deploy model factory on the server side, we assume that you already have a kubernetes cluster ready. If you don't have it, please follow their [website](https://kubernetes.io/).
* **A PV provisioner**: We assume that you have a PV provisioner. We suggest using [nfs-subdir-external-provisioner](https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner) if do not have one yet.
* **A load balancer**: We assume you already have a load balancer deployed in your cluster. We suggest using [metallb](https://metallb.universe.tf/).
* **mongodb**: We assume that you have a mongo db server.
* **AWS S3 or MinIO**: We assume that you have either AWS S3 or MinIO available.
* **Docker Registry**: We assume that you have a docker registry available.

Model factory is verified to be working on both AWS cluster and also any self managed kubernetes cluster. It should also be working with any other environment as well. If you do not have a lot of computing power, you can also set up a minikube and deploy model factory on top of it. Here is a [guide](minikube.md) for the minikube solution.

Before proceeding on the next step, please make sure you can use kubectl to access your k8s cluster on the devvm where you model factory repo is cloned.


## Step 1: Prepare Config File
The first step of deploying model factory is to prepare a config file to tell it your resources.

```
[default]
mf_frontend_endpoint={{mf_frontend_endpoint}}

mongo_db_endpoint={{mongo_db_endpoint}}

docker_registry={{docker_registry}}

s3_endpoint={{s3_endpoint}}
s3_bucket={{s3_bucket}}
aws_access_key_id={{aws_access_key_id}}
aws_secret_access_key={{aws_secret_access_key}}

storage_class={{storage_class}}
```

Please replace all the above variables with real values. Note that you might not know ```mf_frontend_endpoint``` yet, because the model factory frontend service is not created yet. You can leave it empty for now, and we'll come back and fix it later.

## Step 1: Build Base Image
To build the base image, please do:

```
doit build_base_image --verbosity 2
```

## Step 2: Deploy Model Factory Services
To deploy model factory services, please do:

```
doit server --verbosity 2
```

## Step 3: Get Service Endpoints
Before proceeding on the next step, you'll have to understand what endpoint your services are running on.

Use the following command to get the endpoint of this service:

```
kubectl get services -n model-factory-services
```

In my case, the following output is returned:
```
NAME                      TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)          AGE
model-factory-dashboard   LoadBalancer   10.102.106.174   192.168.1.103   8080:31140/TCP   7m22s
model-factory-frontend    LoadBalancer   10.98.125.195    192.168.1.102   5000:32016/TCP   14m
```

which suggests:

* model-factory-frontend's endpoint is http://192.168.1.102:5000
* model-factory-dashboard's endpoint is http://192.168.1.103:8080

Now you have the model factory frontend service endpoint. Please fill it in your ```~/.model_factory.ini``` file, and then repeat step 1 and step 2.


# Client

## Step 1: Prepare Config File
This is the same process as the server side config file setup. If you've done that, just use the file. Otherwise, follow the instruction to create this file.

## Step 2: Install Packages
You'll need to install packages needed by model factory. Please do:

```
doit client --verbosity 2
```

## Step 3: Verify Your Setup
Once you've done the above steps, you are good to go. You can use ```mf job create demo_pipeline``` to create a pipeline job, and then use ```mf job list``` to list the jobs you created.

If you see results from the command, congratulations, your model factory is correctly configured. You can then follow up on the [Development Guide](development_guide.md) to do some model pipeline development.
