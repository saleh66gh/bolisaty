import os
import uuid
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont


def create_ar_text_image(
    text,
    font_path="App/fonts/Cairo-Regular.ttf",
    font_size=24,
    color=(0, 0, 0),
    output_dir="assets/text"
):
    os.makedirs(output_dir, exist_ok=True)

    text = "" if text is None else str(text)
    reshaped = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped)

    font = ImageFont.truetype(font_path, font_size)

    dummy = Image.new("RGBA", (10, 10), (255, 255, 255, 0))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), bidi_text, font=font)

    w = bbox[2] - bbox[0] + 20
    h = bbox[3] - bbox[1] + 20

    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10, 5), bidi_text, font=font, fill=color)

    file_path = os.path.join(output_dir, f"text_{uuid.uuid4().hex}.png")
    img.save(file_path)

    return file_path, w, h