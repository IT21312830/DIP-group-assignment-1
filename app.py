from flask import Flask, render_template, request, redirect, url_for
from PIL import Image, ImageOps
from PIL import ImageFilter, ImageEnhance
import cv2
import numpy as np
import os
import io
import base64
import tensorflow as tf
from tensorflow import keras

app = Flask(__name__)

# Configuration for file uploads
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
            # Save the original image
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], "original.jpg")
            file.save(file_path)

            # Open the original image
            original_image = file_path

    return render_template("index.html", original_image=original_image, modified_image=modified_image)


def load_and_preprocess_images(content_image, style_image):
    # Load the image using PIL
    content_img = Image.open(content_image)
    style_img = Image.open(style_image)

    # Preprocess and convert to NumPy arrays
    content_img = preprocess_image(content_img)
    style_img = preprocess_image(style_img)

    return content_img, style_img

def preprocess_image(image):
    # Resize to match VGG19 input shape
    image = image.resize((224, 224))
    # Convert to NumPy array
    image = np.array(image)
    # Normalize and expand dimensions
    image = image.astype(np.float32) / 255.0
    image = image[tf.newaxis, :]
    return image

def deprocess_image(image):
    image = image[0]
    image = np.clip(image, 0, 1) * 255
    image = image.astype(np.uint8)
    return image

def build_style_transfer_model():
    content_input = keras.layers.Input(shape=(224, 224, 3), name="content_input")
    style_input = keras.layers.Input(shape=(224, 224, 3), name="style_input")

    content_layers = ['block5_conv2']
    style_layers = ['block1_conv1', 'block2_conv1', 'block3_conv1', 'block4_conv1', 'block5_conv1']

    num_content_layers = len(content_layers)
    num_style_layers = len(style_layers)

    vgg19 = keras.applications.VGG19(include_top=False, weights='imagenet', input_tensor=style_input)  # Added input_tensor argument

    style_outputs, content_outputs = StyleContentModel(style_layers, content_layers)([vgg19.output, content_input])  # Used vgg19.output

    return keras.models.Model(inputs=[style_input, content_input], outputs=[style_outputs, content_outputs])

# Other functions (train_step, StyleContentModel) remain the same.

@app.route("/upload", methods=["POST"])
def upload():
    return redirect(url_for("index"))

@app.route("/manipulate", methods=["POST"])
def manipulate():
    color_change = request.form["color_change"]
    rotation = int(request.form["rotation"])
    crop_coords = request.form["crop"].split(',')
    flip = "flip" in request.form

    original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], "original.jpg")
    original_image = Image.open(original_image_path)
    modified_image = original_image.copy()

    if color_change == "bw":
        modified_image = ImageOps.grayscale(modified_image)
    elif color_change == "grayscale":
        modified_image = ImageOps.grayscale(modified_image)

    selected_filter = request.form["filter"]

    if selected_filter == "sharpen":
        enhanced = ImageEnhance.Sharpness(original_image)
        modified_image = enhanced.enhance(2.0)
    elif selected_filter == "smooth":
        modified_image = original_image.filter(ImageFilter.SMOOTH_MORE)
    elif selected_filter == "edges":
        modified_image = original_image.filter(ImageFilter.FIND_EDGES)
    elif selected_filter == "emboss":
        modified_image = original_image.filter(ImageFilter.EMBOSS)
    elif selected_filter == "enhance":
        original_cv = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
        enhanced_cv = cv2.detailEnhance(original_cv, sigma_s=10, sigma_r=0.15)
        modified_image = Image.fromarray(cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2RGB))
    elif selected_filter == "style_transfer":
         # Ensure content and style images have the same size
        style_path = "style_images/style_image.jpeg"    
        content_img = cv2.imread(original_image_path)
        style_img = cv2.imread(style_path)
        content_img = cv2.resize(content_img, (style_img.shape[1], style_img.shape[0]))

        # Apply a simple blending method
        alpha = 0.7  # Adjust the blending factor
        result = cv2.addWeighted(content_img, alpha, style_img, 1 - alpha, 0)
        modified_image = Image.fromarray(result)
    else:
        modified_image = original_image

    modified_image = modified_image.rotate(rotation, expand=True)

    if crop_coords and len(crop_coords) == 4:
        crop_coords = [int(coord) for coord in crop_coords]
        modified_image = modified_image.crop(crop_coords)

    if flip:
        modified_image = ImageOps.invert(modified_image)

    # Save the modified image to a BytesIO object
    output = io.BytesIO()
    modified_image.save(output, format="JPEG")
    output.seek(0)

    return render_template("index.html", original_image=f"/{app.config['UPLOAD_FOLDER']}/original.jpg",
                           modified_image=f"data:image/jpeg;base64,{base64.b64encode(output.read()).decode()}")

if __name__ == "__main__":
    app.debug = True  # Enable debug mode
    app.run()
