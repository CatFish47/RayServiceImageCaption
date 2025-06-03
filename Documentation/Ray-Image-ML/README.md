# Junkyard K8s + Ray MVP

For the MVP, I made a simple example using an out-of-the-box image captioning model to prove the ability to pass in an image and receive text as an output. This repo includes the code (a python file), required packages (requirements.txt), a zip (containing the python file and the requirements.txt file) and a YAML file for ray service.

To start up the Ray Service, run the command below:

```bash
kubectl apply -f https://raw.githubusercontent.com/CatFish47/RayServiceImageCaption/refs/heads/main/rayservice-caption.yaml
```

Next, run (assumes you have a curl pod up)

```bash
kubectl exec curl -- \
curl -sS -X POST -H 'Content-Type: application/json' \
image-classification-serve-svc:8000/image-classification/ \
-d '{"url": "https://hips.hearstapps.com/hmg-prod/images/dog-puppy-on-garden-royalty-free-image-1586966191.jpg"}'
```

You should see in the output something like this:

```bash
# {"prediction":["n02099601","golden_retriever",0.730442464351654]}
```