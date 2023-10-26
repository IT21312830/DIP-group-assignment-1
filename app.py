from flask import Flask, render_template, request, redirect, url_for
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import os
import io
import base64

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

@app.route("/", methods=["GET", "POST"])
def index():
    original_image = None
    modified_image = None

    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)
        
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)
        
        if file:
            file_path = f"{app.config['UPLOAD_FOLDER']}/original.jpg"
            file.save(file_path)
            original_image = file_path
            
    return render_template("index.html", original_image=original_image, modified_image=modified_image)

@app.route("/manipulate", methods=["POST"])
def manipulate():
    color_change = request.form["color_change"]
    rotation = int(request.form["rotation"])
    crop_coords = request.form["crop"].split(',')
    flip = "flip" in request.form
    sharpen_factor = float(request.form["sharpen"])
    blur_factor = float(request.form["blur"])
    edge_detection = "edge_detection" in request.form

    original_image = Image.open(f"{app.config['UPLOAD_FOLDER']}/original.jpg")
    modified_image = original_image.copy()

    if color_change == "bw":
        modified_image = ImageOps.grayscale(modified_image)
    elif color_change == "grayscale":
        modified_image = ImageOps.grayscale(modified_image)

    modified_image = modified_image.rotate(rotation, expand=True)

    if crop_coords and len(crop_coords) == 4:
        crop_coords = [int(coord) for coord in crop_coords]
        modified_image = modified_image.crop(crop_coords)

    if flip:
        modified_image = ImageOps.invert(modified_image)

    if edge_detection:
        modified_image = modified_image.filter(ImageFilter.FIND_EDGES)

    if sharpen_factor != 1.0:
        sharpness = ImageEnhance.Sharpness(modified_image)
        modified_image = sharpness.enhance(sharpen_factor)

    if blur_factor > 1.0:
        modified_image = modified_image.filter(ImageFilter.GaussianBlur(radius=blur_factor))

    contrast_factor = float(request.form["contrast"])
    contrast_enhancer = ImageEnhance.Contrast(modified_image)
    modified_image = contrast_enhancer.enhance(contrast_factor)

    brightness_factor = float(request.form["brightness"])
    brightness_enhancer = ImageEnhance.Brightness(modified_image)
    modified_image = brightness_enhancer.enhance(brightness_factor)

    output = io.BytesIO()
    modified_image.save(output, format="JPEG")
    output.seek(0)

    return render_template("index.html", original_image=f"/{app.config['UPLOAD_FOLDER']}/original.jpg",
                           modified_image=f"data:image/jpeg;base64,{base64.b64encode(output.read()).decode()}")

if __name__ == "__main__":
    app.run(debug=True)
