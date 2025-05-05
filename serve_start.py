import ray
from ray import serve
from caption_service import CaptionModel

ray.init()
serve.run(CaptionModel.bind())
