# Ray Text ML Hello World

While the Hello World application from the tutorial was a good proof of concept for a test application, there is no ML involved in the setup and creation of that RayService. The goal is to use the example Text ML example here to create a service.

Before we begin, make sure you have setup the Ray operator as stated in the Ray setup. This example also has the same name as the Ray service in the example before, so make sure you clean that up by doing `kubectl delete rayservice rayservice-sample`.

Start by downloading the yaml file:

```bash
wget https://raw.githubusercontent.com/ray-project/kuberay/1283a62269c09aeff38b54db4400786512c46210/ray-operator/config/samples/ray-service.text-ml.yaml
```

Open up a file editor and replace the two instances where it says `image: rayproject/ray:2.41.0` with `image: rayproject/ray:2.41.0-py39-aarch64`. This is to ensure that it installs the docker image that matches our python version and, more importantly, architecture.

If you try to apply the YAML file as is, you will run into a health probe problem. This is because the YAML file doesn’t specify the command to run for the health probe by default, and for some reason the default command that it runs is buggy. As such, we need to specify our own health probe. To do so, add to the YAML file so that it looks like below. This should be located under the `workerGroupSpecs` section.

```yaml
        template:
          spec:
            containers:
              - name: ray-worker # must consist of lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name',  or '123-abc'
                image: rayproject/ray:2.41.0-py39-aarch64
                readinessProbe:
                  exec:
                    command:
                      - bash
                      - -c
                      - wget -T 2 -q -O- http://localhost:52365/api/local_raylet_healthz | grep success
                resources:
                  limits:
                    cpu: "1"
                    memory: "2Gi"
                  requests:
                    cpu: "500m"
                    memory: "2Gi"
```

Apply it with

```bash
kubectl apply -f ray-service.text-ml.yaml
```

Now that the node is running, assuming you have a curl node running, run the following to test it out. You should get a French translation of the input sentence.

```bash
kubectl exec curl -- curl -sS -X POST -H 'Content-Type: application/json' rayservice-sample-serve-svc:8000/summarize_translate/ -d '["This is an example sentence in English"]'
# Il s'agit d'une phrase d'exemple en anglais.
```

We will be using this YAML file + code as the basis for our image-to-text model POC.