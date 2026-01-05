from PIL import Image
import os

def compress_jpeg(
    input_path,
    output_path,
    quality=70,        # 60–75 is a good range
    max_size=None      # e.g. (1024, 1024) or None
):
    with Image.open(input_path) as img:
        img = img.convert("RGB")

        if max_size:
            img.thumbnail(max_size, Image.LANCZOS)

        img.save(
            output_path,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True
        )

# Example
compress_jpeg(
    "fixed_image.jpg",
    "fixed_image_compressed.jpg",
    quality=70,
    max_size=(1024, 1024)
)

from PIL import Image
import os

bad_img = "IMG_1958.HEIC"  # renamed file

img = Image.open(bad_img)
img.convert("RGB").save("nextrex4.jpg", "JPEG")