# Ray Setup and Hello World

For FishSense, since we only care about hosting pre-trained models for inference, we should be intimately familiar with Ray Serve. Here is the [quickstart guide for Ray Serve](https://docs.ray.io/en/latest/serve/index.html).

## Setup

For starters, ensure that you have a K8s cluster with helm installed. If not, follow the “Setting up Kubernetes” guide.

Following the setup for [KubeRay](https://docs.ray.io/en/latest/cluster/kubernetes/getting-started.html), we will mainly need [RayService](https://docs.ray.io/en/latest/cluster/kubernetes/getting-started/rayservice-quick-start.html), the method by which we will do distributed serving of models on the Kubernetes cluster.

First, install the Kuberay Operator (taken straight from the docs)

```bash
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update

# Install both CRDs and KubeRay operator v1.3.0.
helm install kuberay-operator kuberay/kuberay-operator --version 1.3.0

# Confirm that the operator is running in the namespace `default`.
kubectl get pods
# NAME                                READY   STATUS    RESTARTS   AGE
# kuberay-operator-7fbdbf8c89-pt8bk   1/1     Running   0          27s
```

Next, start up RayService. For the phones, we are likely going to need the arm architecture version of the image (which differs from the default), so we’ll follow these instructions:

```bash
wget https://raw.githubusercontent.com/ray-project/kuberay/v1.3.0/ray-operator/config/samples/ray-service.sample.yaml
vi ray-service.sample.yaml
# edit the two instances of where it sets the container image to ray:2.41.0 -- set it instead to 2.41.0-py39-aarch64
```

Once you’ve updated that, apply it to start the service

```bash
# If you didn't encounter any issues pulling images and starting container
kubectl apply -f ray-service.sample.yaml
```

At this point, if you run `kubectl get rayclusters`, it should look like this

```bash
NAME                                 DESIRED WORKERS   AVAILABLE WORKERS   CPUS    MEMORY   GPUS   STATUS   AGE
rayservice-sample-raycluster-hw7xw   1                 1                   2500m   4Gi      0      ready    7m13s
```

## Hello World

To test that your setup works properly, we are going to send requests to the Serve applications by the Kubernetes serve service. Run the following commands:

```bash
# Run a curl pod
kubectl run curl --image=curlimages/curl-base:latest --command -- tail -f /dev/null

# Send a request to the sample calculator app
kubectl exec curl -- curl -sS -X POST -H 'Content-Type: application/json' rayservice-sample-serve-svc:8000/calc/ -d '["MUL", 3]'
# You should get a result that says:
15 pizzas please!

# Send a request to the fruits stand app
kubectl exec curl -- curl -sS -X POST -H 'Content-Type: application/json' rayservice-sample-serve-svc:8000/fruit/ -d '["MANGO", 2]'
# You should get a result that says:
6
```

## Explanation

To explain what’s happening here, there are two major things to note: KubeRay operator that was setup and the RayService that was setup. The operator oversees/manages the custom resource that is the RayService. The RayService, based on [this YAML file](https://raw.githubusercontent.com/ray-project/kuberay/v1.3.0/ray-operator/config/samples/ray-service.sample.yaml), tells Ray Serve to launch 2 apps (`fruit_app` and `math_app`), load the code from GitHub, and create/scale specific deployments. These deployments start inside the head node’s Ray runtime. Inside the Ray head node, a Serve HTTP server listens on port 8000. The curl pod is then setup to send HTTP requests to the apps.

## Troubleshooting

### CrashLoopBackOff

If you are experiencing repeated crashing (`CrashLoopBackOff`), check the details with `kubectl describe pod <pod-name>`. If you are getting an event logged such as `Liveness probe failed: Get "http://192.168.1.2:8080/metrics": dial tcp 192.168.1.2:8080: connect: no route to host`, that’s because the health probe can’t reach that address. To fix it, set the address to probe to localhost instead by running the command below.

```bash
helm upgrade --install kuberay-operator kuberay/kuberay-operator \
  --version 1.3.0 \
  --set livenessProbe.httpGet.host=localhost \
  --set readinessProbe.httpGet.host=localhost
```

### ImagePullBackOff

If your raycluster worker is failing to initialize and you get this error, this means that phones don’t have the internet capacity to pull the images since the images are ~2GB in size. To fix this, follow these steps:

```bash
# On a machine with docker (i.e. your computer)
docker pull rayproject/ray:2.41.0-py39-aarch64
docker save rayproject/ray:2.41.0-py39-aarch64 -o ray-2.41.0-aarch64.tar

# SCP it into the phone you are working on (control plane)
scp ray-2.41.0-aarch64.tar automaton:/tmp/
# on automaton...
scp /tmp/ray-2.41.0-aarch64.tar <node>:/tmp/

# in the phone
sudo ctr image import /tmp/ray-2.41.0-aarch64.tar

# then run this:
helm upgrade --install raycluster kuberay/ray-cluster \
  --version 1.3.0 \
  --set image.repository=rayproject/ray \
  --set image.tag=2.41.0-py39-aarch64 \
  --set head.rayStartParams.dashboard-host=0.0.0.0

# restart delete the old raycluster workers to initialize new
# ones with the new image
kubectl delete pod raycluster-kuberay-head-<ID> raycluster-kuberay-workergroup-worker-<ID>
```
