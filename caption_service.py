import tempfile
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import (
    preprocess_input,
    decode_predictions,
    MobileNetV2,
)
from ray import serve

@serve.deployment()
class ImageClassifier:
    def __init__(self):
        self.model = MobileNetV2(weights="imagenet")

    # Users can send HTTP requests with an image. The classifier will return
    # the top prediction.
    # Sample output: {"prediction":["n02099601","golden_retriever",0.17944198846817017]}
    
    async def __call__(self, http_request):
        request = await http_request.form()
        image_file = await request["image"].read()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(image_file)
            temp_file.close()
            temp_file_path = temp_file.name
            img = image.load_img(temp_file_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = self.model.predict(x)
        decoded_preds = decode_predictions(preds, top=1)[0]
        return {"prediction": decoded_preds[0]}


app = ImageClassifier.bind()


# from ray import serve
# from ray.serve.handle import DeploymentHandle
# from starlette.requests import Request

# from typing import Dict, Any
# from PIL import Image
# import requests
# import io
# import base64
# import torch
# from transformers import CLIPProcessor, CLIPModel, GPT2Tokenizer, GPT2LMHeadModel

# # Component 1: CLIP Encoder
# @serve.deployment
# class ClipEncoder:
#     def __init__(self):
#         self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
#         self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
#         self.model.eval()

#     def encode_image(self, image: Image.Image):
#         inputs = self.processor(images=image, return_tensors="pt")
#         with torch.no_grad():
#             return self.model.get_image_features(**inputs)

# # Component 2: GPT-2-based Caption Generator
# @serve.deployment
# class CaptionGenerator:
#     def __init__(self):
#         self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
#         self.model = GPT2LMHeadModel.from_pretrained("gpt2")
#         self.model.eval()

#     def generate_caption(self, prompt: str) -> str:
#         input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
#         with torch.no_grad():
#             output = self.model.generate(input_ids, max_length=20, num_beams=5, early_stopping=True)
#         return self.tokenizer.decode(output[0], skip_special_tokens=True)

# # Component 3: Main service handler
# @serve.deployment(route_prefix="/caption")
# class ImageCaptionService:
#     def __init__(
#         self,
#         encoder: DeploymentHandle,
#         generator: DeploymentHandle
#     ):
#         self.encoder = encoder.options(use_new_handle_api=True)
#         self.generator = generator.options(use_new_handle_api=True)

#     async def __call__(self, request: Request) -> Dict[str, Any]:
#         data = await request.json()
#         image_url = data.get("url")
#         image_b64 = data.get("image_b64")

#         if image_url:
#             image = Image.open(requests.get(image_url, stream=True).raw)
#         elif image_b64:
#             image_bytes = base64.b64decode(image_b64)
#             image = Image.open(io.BytesIO(image_bytes))
#         else:
#             return {"error": "Provide either 'url' or 'image_b64'"}

#         # We won't pass image features explicitly because GPT-2 can't use them directly.
#         # We'll simulate the interaction by hardcoding a prompt from the encoder stage.
#         # In a more advanced system, you'd use a cross-modal model like BLIP.

#         # Simulate encoder + generator workflow
#         await self.encoder.encode_image.remote(image)  # For future integration
#         caption = await self.generator.generate_caption.remote("A photo of")

#         return {"caption": caption}

# # Bind the deployments like in FruitMarket example
# encoder = ClipEncoder.bind()
# generator = CaptionGenerator.bind()
# app = ImageCaptionService.bind(encoder, generator)