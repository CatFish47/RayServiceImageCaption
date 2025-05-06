from ray import serve
from fastapi import Request
from PIL import Image
import requests
import io
import base64
import torch
from transformers import CLIPProcessor, CLIPModel, GPT2Tokenizer, GPT2LMHeadModel

@serve.deployment(route_prefix="/caption", num_replicas=1)
class CaptionModel:
    def __init__(self):
        # Load the pre-trained CLIP model and processor
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # Load the pre-trained GPT-2 model and tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        self.gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2")
        
        # Set models to evaluation mode
        self.clip_model.eval()
        self.gpt2_model.eval()

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

        # Preprocess the image for CLIP
        inputs = self.clip_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)

        # Generate a prompt for GPT-2 using the image features
        # Note: In practice, you'd need a method to convert image features to a textual prompt
        # For demonstration, we'll use a placeholder prompt
        prompt = "A photo of"

        # Tokenize the prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")

        # Generate caption using GPT-2
        with torch.no_grad():
            output = self.gpt2_model.generate(input_ids, max_length=20, num_beams=5, early_stopping=True)
        caption = self.tokenizer.decode(output[0], skip_special_tokens=True)

        return {"caption": caption}

app = CaptionModel.bind()