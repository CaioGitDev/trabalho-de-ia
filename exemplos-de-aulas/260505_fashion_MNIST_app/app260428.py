from flask import Flask, request, render_template
import tensorflow as tf
from PIL import Image
import numpy as np

app = Flask(__name__)

# Load the previously saved model
# Transfer Learning
model = tf.keras.models.load_model\
    ('fashion_mnist_8_consistent_sub_layers.keras')

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
            image = Image.open(file.stream).convert('L').resize((28, 28))
            image = np.expand_dims(image, axis=0)
            image = np.array(image) / 255.0

            predictions = model.predict(image)
            predictions = model.predict(image)
            predicted_class = class_names[np.argmax(predictions)]

            return predicted_class

    return render_template('upload.html')


if __name__ == '__main__':
    app.run(
        debug=True,
        port=5005
    )
