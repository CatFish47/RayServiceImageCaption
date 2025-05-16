from fastapi import FastAPI
from image_class import app
from ray import serve

fast_app = FastAPI()
serve.run(app, name="image-classification", route_prefix="/image-classification")