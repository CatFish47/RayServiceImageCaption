# FishSense MVP

For FishSense, we successfully ran the code from the [FishSense Lite repo](https://github.com/UCSD-E4E/fishsense-lite/tree/main) on the cluster. To do so, you will need at least 4 nodes: 1 for the Kuberay operator, 1 for the head node, and 2 worker nodes. Due to the intense memory requirements of FishSense, these will each need their own node in order to maximum the amount of RAM each node can use.

To install and run FishSense on the cluster, we will use Helm. The command can be found below.

```bash
helm install raycluster kuberay/ray-cluster \
  --version 1.1.0 \
  --set image.repository=ghcr.io/ucsd-e4e/fishsense \
  --set image.tag=ray-cpu \
  --set head.resources.limits.cpu=4 \
  --set head.resources.limits.memory=10G \
  --set head.resources.requests.cpu=1 \
  --set head.resources.requests.memory=10G \
  --set worker.resources.limits.cpu=4 \
  --set worker.resources.limits.memory=10G \
  --set worker.resources.requests.cpu=1 \
  --set worker.resources.requests.memory=10G \
  --set head.ray_start_params.num-cpus=0 \
  --set worker.minReplicas=2 \
  --set worker.replicas=2
```

This command creates a Ray cluster with the FishSense code. It's important to note that we set the memory requests and limits for both the head and the worker to 10G. Since the phones only have 11GB of RAM, we need to maximum the amount of memory each worker + head has access to. We also set the number of workers to 2 in order to increase the parallelization of the task. If more nodes are available, you can increase the number of replicas.

You will need to prepare a config YAML file for FishSense to actually run FishSense. To obtain a config file, please contact those in charge of the [FishSense repository](https://github.com/UCSD-E4E/fishsense-lite/tree/main). The config file should look something like below:

```yaml
input_filesystem:
  protocol: ... (e.g. smb [Samba])
  kwargs:
    host: ...
    username: ...
    password: ...

output_filesystem:
  protocol: ...
  kwargs:
    host: ...
    username: ...
    password: ...

jobs:
  - display_name: Name
    job_name: name
    parameters:
      data:
        - ...
      lens-calibration: ...
      output: ...
```

Once you have this file, copy it into the head node and run FishSense with the following commands:

```bash
kubectl cp preprocess.yaml <head node name>:/tmp
kubectl exec -it <head node name> -- /bin/bash

# in the head node
fsl run-jobs /tmp/preprocess.yaml
```

If all things go well, the job should take input files from the input file system, process it, and put it in the output filesystem.