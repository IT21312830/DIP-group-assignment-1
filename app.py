from flask import Flask, render_template, request, redirect, url_for
from PIL import Image, ImageOps, ImageFilter
import os
import io
import base64

app = Flask(__name__)

# Configuration for file uploads
app.config["UPLOAD_FOLDER"] = "static/uploads"


@app.route("/", methods=["GET", "POST"])
def index():
    original_image = None
    modified_image = None

    if request.method == "POST":
        # Check if a file was uploaded
        if "file" not in request.files:
            return redirect(request.url)

        # retrieves the uploaded file from the POST request.
        file = request.files["file"]

        # checks if the uploaded file has a filename. If not redirect
        if file.filename == "":
            return redirect(request.url)

        if file:
            # Save the original image
            file_path = f"{app.config['UPLOAD_FOLDER']}/original.jpg"
            file.save(file_path)

            # Open the original image
            original_image = file_path

    return render_template("index.html", original_image=original_image, modified_image=modified_image)


@app.route("/upload", methods=["POST"])
def upload():
    return redirect(url_for("index"))


@app.route("/manipulate", methods=["POST"])
def manipulate():
    color_change = request.form["color_change"]
    rotation = int(request.form["rotation"])
    crop_coords = request.form["crop"].split(',')
    flip = "flip" in request.form
    smoothing = "smoothing" in request.form
    embossing = "embossing" in request.form

    # Open the original image
    original_image = Image.open(f"{app.config['UPLOAD_FOLDER']}/original.jpg")

    # Perform manipulations
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

    if smoothing:
        modified_image = modified_image.filter(ImageFilter.SMOOTH)

    if embossing:
        modified_image = modified_image.filter(ImageFilter.EMBOSS)

    # Save the modified image to a BytesIO object
    output = io.BytesIO()
    modified_image.save(output, format="JPEG")
    output.seek(0)

    return render_template(
        "index.html",
        original_image=f"/{app.config['UPLOAD_FOLDER']}/original.jpg",
        modified_image=f"data:image/jpeg;base64,{base64.b64encode(output.read()).decode()}",
    )


if __name__ == "__main__":
    app.run(debug=True)
