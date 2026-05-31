# cifar10_w_predict_v2.py

import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np

# Check if TensorFlow can access the GPU
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

# Load CIFAR-10 dataset
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()

x_train_display, x_test_display = x_train.copy(), x_test.copy()
x_train, x_test = x_train / 255.0, x_test / 255.0

# Class names for CIFAR-10
class_names = [
    'airplane',
    'automobile',
    'bird',
    'cat',
    'deer',
    'dog',
    'frog',
    'horse',
    'ship',
    'truck'
]

# Display some sample images from the dataset
def plot_sample_images(x, y, class_names, num_rows=3, num_cols=5):
    plt.figure(figsize=(10, 6))
    for i in range(num_rows * num_cols):
        plt.subplot(num_rows, num_cols, i + 1)
        plt.xticks([])
        plt.yticks([])
        plt.grid(False)
        plt.imshow(x[i])
        plt.xlabel(class_names[y[i][0]])
    plt.tight_layout()
    plt.show()
# def plot_sample_images

# Plot some images from the training set
plot_sample_images(x_train, y_train, class_names)

# Normalize the pixel values (2 normalizations?! "everything is a frog")
# x_train, x_test = x_train / 255.0, x_test / 255.0

# A kernel is a pattern detector sliding across the image - "a small window sliding over the image";
# filters is "how many different detectors to run simultaneously"
# pooling mathematically shrinks the result to force the network to care about what was found, NOT exactly where

# Define the model using Sequential API with an explicit InputLayer
model = tf.keras.Sequential([
    # raw pixels
    tf.keras.layers.InputLayer(input_shape=(32, 32, 3), name='input_layer'),

    # Edges, color changes
    # 32 filters scan for 32 different low-level features
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', name='conv1'),
    # halve the map: 32×32 => 16×16
    tf.keras.layers.MaxPooling2D((2, 2), name='pool1'),

    # Corners, textures, simple shapes
    # 64 filters now look for combinations of those features
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu', name='conv2'),
    # halve again: 16×16 => 8×8
    tf.keras.layers.MaxPooling2D((2, 2), name='pool2'),

    # Object parts: wheels, ears, wings
    # deeper patterns — parts of objects
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu', name='conv3'),
    # unroll into a vector for the Dense layers
    tf.keras.layers.Flatten(name='flatten'),

    # Full object classification
    tf.keras.layers.Dense(64, activation='relu', name='dense1'),
    tf.keras.layers.Dropout(0.5, name='dropout1'), # combat overfitting

    # Result
    tf.keras.layers.Dense(10, name='output_layer')
])

# Print the model summary
model.summary()

# Compile the model
model.compile(
    optimizer='adam',
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy']
)

########################################################################################################################
# Train the model
"""
history = model.fit(
    x_train,
    y_train,
    epochs=10,  # more epochs for better learning
    validation_data=(x_test, y_test) # bad methodology - Seeing test data during training, even just for monitoring
)
"""

########################################################################################################################
from sklearn.model_selection import train_test_split
x_train, x_val, y_train, y_val = train_test_split(
    x_train,
    y_train,
    test_size=0.1,
    random_state=123
)

history = model.fit(
    x_train, y_train,
    # epochs=50,
    epochs=10,
    validation_data=(x_val, y_val), # true held-out val set
)

########################################################################################################################



# Evaluate the model
test_loss, test_acc = model.evaluate(
    x_test,
    y_test,
    verbose=2
)
print(f'\nTest accuracy: {test_acc}')

# Plot training & validation accuracy values
def plot_training_history(history):
    plt.figure(figsize=(8, 6))
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Model Accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(loc='upper left')
    plt.show()
# def plot_training_history

plot_training_history(history)

# Test the model with new samples (using the test set here)
predictions = model.predict(x_test)

# Display predictions for the first 5 test samples
def display_predictions(x, y_true, y_pred, class_names, num_samples=5):
    plt.figure(figsize=(10, 6))
    for i in range(num_samples):
        plt.subplot(1, num_samples, i + 1)
        plt.xticks([])
        plt.yticks([])
        plt.grid(False)
        plt.imshow(x[i])
        true_label = class_names[y_true[i][0]]
        predicted_label = class_names[np.argmax(y_pred[i])]
        plt.xlabel(f'True: {true_label}\nPred: {predicted_label}')
    plt.tight_layout()
    plt.show()
# display_predictions

display_predictions(
    x_test_display,
    y_test,
    predictions,
    class_names
)


########################################################################################################################
from confusion_matrix2 import \
    confusion_matrix, \
    confusion_matrix_to_string, \
    confusion_matrix_metrics, \
    get_all_model_performance_metrics_for_all_classes, \
    present_performance_metrics

# ─────────────────────────────────────────────────────────────────────────────
# Confusion Matrix — CIFAR-10 Test Set

# Step 1 - Collapse logit vectors => predicted class indices
# predictions shape is (N, 10); argmax picks the highest-scoring class
predicted_class_indices = np.argmax(predictions, axis=1)

# Step 2 - Convert to Python lists of strings
# CIFAR-10 y_test shape is (N, 1) — flatten() removes the extra dimension
# We use class_names so the matrix shows "cat", "dog" etc. instead of "3", "5"
actual_as_strings    = [class_names[i] for i in y_test.flatten()]
predicted_as_strings = [class_names[i] for i in predicted_class_indices]

# Step 3 - Build and print the confusion matrix
print("\n" + "=" * 60)
print("CONFUSION MATRIX — CIFAR-10 TEST SET")
print("=" * 60)

cm = confusion_matrix(
    actual_as_strings,
    predicted_as_strings
)

cms = confusion_matrix_to_string(
    cm,
    actual_as_strings
)
print("\nConfusion matrix (rows=actual, cols=predicted):")
print(cms)

# Step 4 - Compute TP / FP / FN / TN per class
metrics = confusion_matrix_metrics(
    cm,
    actual_as_strings
)

# Step 5 - Compute and display accuracy / precision / recall / F1 per class
performance = get_all_model_performance_metrics_for_all_classes(
    p_metrics=metrics,
    p_dataset=actual_as_strings
)
present_performance_metrics(performance)
