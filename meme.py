from PIL import Image
import requests
from io import BytesIO
import binascii
from datetime import datetime, timedelta, date


class Meme:

    def __init__(self, title, img_url):
        self.title = title
        self.img_url = img_url

    def get_image(self):
        # Return image in a format it can be uploaded directly to Facebook via graph API
        img = Image.open(requests.get(self.img_url, stream=True).raw)
        img = img.convert('RGB')
        byteio = BytesIO()
        img.save(byteio, format='PNG')
        return byteio.getvalue()
