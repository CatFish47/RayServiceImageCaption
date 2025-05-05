from ray import serve
from fastapi import Request
from PIL import Image
import requests
import io
import base64

@serve.deployment(route_prefix="/caption", num_replicas=1)
class CaptionModel:
    def __init__(self):
        from transformers import BlipProcessor, BlipForConditionalGeneration
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    async def __call__(self, request: Request):
        data = await request.json()
        image_url = data.get("url")
        image_b64 = data.get("image_b64")

        if image_url:
            image = Image.open(requests.get(image_url, stream=True).raw)
        elif image_b64:
            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes))
        else:
            return {"error": "Provide either 'url' or 'image_b64'"}

        inputs = self.processor(image, return_tensors="pt")
        out = self.model.generate(**inputs)
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return {"caption": caption}

app = CaptionModel.bind()