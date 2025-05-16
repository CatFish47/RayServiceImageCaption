import tempfile
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import (
    preprocess_input,
    decode_predictions,
    MobileNetV2,
)
from ray import serve
import requests
from io import BytesIO
from PIL import Image
from fastapi import Request

@serve.deployment()
class ImageClassifier:
    def __init__(self):
        self.model = MobileNetV2(weights="imagenet")

    async def __call__(self, http_request: Request):
        # Try to parse JSON with a 'url' key
        try:
            json_data = await http_request.json()
            image_url = json_data.get("url")
        except Exception:
            image_url = None

        if image_url:
            # Load image from URL
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content)).convert("RGB")
            img = img.resize((224, 224))
        else:
            # Load image from uploaded form file
            form = await http_request.form()
            image_file = await form["image"].read()
            img = Image.open(BytesIO(image_file)).convert("RGB")
            img = img.resize((224, 224))

        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = self.model.predict(x)
        decoded_preds = decode_predictions(preds, top=1)[0]
        return {"prediction": decoded_preds[0]}

app = ImageClassifier.bind()