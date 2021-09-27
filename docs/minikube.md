This doc explains how you can prepare the model factory prerequisite resources on a single linux box. The instructions are based on ubuntu 20.04. You need at least 4 cpus and 8G memory.


# Install Docker Registry
Before creating the docker registry, let's add the insecure docker registry to your devvm. (Note that your devvm might have multiple IP addresses. Use the one that is accessible from your subnet. If you are doing it at home, go with the 192.168 one)

```
echo '{"insecure-registries" : ["{YOUR_DEVVM_IP}:5000"]}' > docker_daemon.json
sudo mv docker_daemon.json /etc/docker/daemon.json
```

After that, restart your docker service
```
sudo systemctl restart docker
```

To install docker registry, use the following commands:

```
docker run -d -p 5000:5000 --name registry registry:2
```

Once this is done, your docker registry is up and running. Your docker registry's endpoint is {YOUR_DEVVM_IP}:5000.


# Install Minikube
To install minikube, use the following commands

```
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube_latest_amd64.deb
sudo dpkg -i minikube_latest_amd64.deb
```

To start the minikube, use the following commands
```
minikube start --insecure-registry "{YOUR_DEVVM_IP}:5000" --addons default-storageclass --addons metallb --addons storage-provisioner --cpus 4 --memory "8G"
```

Once your minikube cluster is up, use the following command to check its subnet:

```
minikube profile list
```

In my case, the output is
```
|----------|-----------|---------|--------------|------|---------|---------|-------|
| Profile  | VM Driver | Runtime |      IP      | Port | Version | Status  | Nodes |
|----------|-----------|---------|--------------|------|---------|---------|-------|
| minikube | docker    | docker  | 192.168.49.2 | 8443 | v1.22.2 | Running |     1 |
|----------|-----------|---------|--------------|------|---------|---------|-------|
```
which suggest that the minikube is in the 192.168.49.0/24 subnet.

Configure your metallb load balancer with this command
```
kubectl edit configmap config -n metallb-system
```

In my case, the config is
```
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
#
apiVersion: v1
data:
  config: |
    address-pools:
    - name: default
      protocol: layer2
      addresses:
      - -
kind: ConfigMap
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","data":{"config":"address-pools:\n- name: default\n  protocol: layer2\n  addresses:\n  - -\n"},"kind":"ConfigMap","metadata":{"annotations":{},"name":"config","namespace":"metallb-system"}}
  creationTimestamp: "2021-09-24T20:11:36Z"
  name: config
  namespace: metallb-system
  resourceVersion: "328"
  uid: 7276ae84-2933-44a4-aa74-b87fd01a31dd

```

Fill the addresses with ```192.168.49.11 - 192.168.49.20```, so that metallb can allocate address for us.


# Install MongoDB

Use the following command to install mongodb
```
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt update && sudo apt install mongodb-org -y
```

Set the net.bindIp to 0.0.0.0 by updating /etc/mongod.conf.

Then start mongodb
```
sudo systemctl start mongod.service
```

# Install MinIO
Use the following commands to install minio.

```
docker run -d -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

Go into the minio dashboard do the followings:

* Create a minio service account, write down the access key and secret.
* Create a bucket with its name as model-factory.
