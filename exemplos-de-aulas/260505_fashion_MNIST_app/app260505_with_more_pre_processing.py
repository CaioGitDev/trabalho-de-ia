from flask import Flask, request, render_template
import tensorflow as tf
from PIL import Image, ImageOps, ImageEnhance
import numpy as np

app = Flask(__name__)

# Load the previously saved model
model = tf.keras.models.load_model(
    'fashion_mnist_8_consistent_sub_layers.keras'
)

# Define class names
class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']


@app.route('/', methods=['GET', 'POST'])
def upload_predict():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'

        file = request.files['file']

        if file.filename == '':
            return 'No selected file'

        if file:
            # PP Step 1: Convert to greyscale and resize to 28x28
            image = Image.open(file.stream).convert('L').resize((28, 28))

            # Step 2: Auto-invert if background is light (i.e. a photo/drawing)
            # Fashion-MNIST: mean pixel is LOW (dark background)
            # Hand drawing:  mean pixel is HIGH (white paper background)
            image_array = np.array (image)
            if image_array.mean () > 127:
                image = ImageOps.invert (image)
            # if

            # PP Step 3: Boost contrast to push pixels toward sharp black/white
            image = ImageEnhance.Contrast(image).enhance(2.0)

            # PP Step 4: Normalise to [0, 1] and add batch dimension
            image = np.array(image) / 255.0
            image = np.expand_dims(image, axis=0)

            # Step 5: Predict
            predictions = model.predict(image)
            predicted_class = class_names[np.argmax(predictions)]

            return predicted_class
        # if file
    # if POST

    return render_template('upload.html')
# def upload_predict

if __name__ == '__main__':
    app.run(
        debug=True,
        port=5005
    )
