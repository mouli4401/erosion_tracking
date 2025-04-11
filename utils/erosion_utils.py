import numpy as np
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import datetime

RESIZE_DIM = (128, 128)

def calculate_erosion_metrics(before_image, after_image):
    before = np.array(before_image.resize(RESIZE_DIM))
    after = np.array(after_image.resize(RESIZE_DIM))
    diff = np.abs(after.astype(int) - before.astype(int))
    erosion_mask = np.mean(diff, axis=2) > 25
    return erosion_mask, np.sum(erosion_mask)

def generate_overlay(image, mask):
    image = image.resize(RESIZE_DIM).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width = mask.shape[1]
    cutoff_x = width // 2

    for y in range(mask.shape[0]):
        for x in range(cutoff_x, width):
            if mask[y, x]:
                draw.point((x, y), fill=(255, 0, 0, 120))

    combined = Image.alpha_composite(image, overlay)
    return combined

def get_sentinel_image(lat_min, lat_max, lon_min, lon_max):
    INSTANCE_ID = "e5518db2-221f-4790-8c86-b26caefec6e7"  # Replace with your real instance ID
    LAYER = "1_TRUE_COLOR"
    URL = f"https://services.sentinel-hub.com/ogc/wms/{INSTANCE_ID}"
    today = datetime.date.today().isoformat()
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "BBOX": f"{lat_min},{lon_min},{lat_max},{lon_max}",
        "LAYERS": LAYER,
        "MAXCC": 20,
        "WIDTH": 256,
        "HEIGHT": 256,
        "FORMAT": "image/png",
        "CRS": "EPSG:4326",
        "TIME": today,
        "VERSION": "1.3.0"
    }
    try:
        response = requests.get(URL, params=params)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Sentinel image fetch error: {e}")
        return None
