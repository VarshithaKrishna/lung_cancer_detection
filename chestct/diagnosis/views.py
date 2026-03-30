import tensorflow as tf
import numpy as np
import cv2
import joblib
import os
from PIL import Image
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from tensorflow.keras.applications.vgg16 import preprocess_input
import matplotlib.pyplot as plt
import seaborn as sns

# --- Auth views ---
def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('upload_ct')
    else:
        form = UserCreationForm()
    return render(request, 'diagnosis/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('upload_ct')
    else:
        form = AuthenticationForm()
    return render(request, 'diagnosis/login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('login')

def home(request):
    return render(request, 'diagnosis/home.html')

def know_more(request, diagnosis):
    template_map = {
        "adenocarcinoma": "diagnosis/know_more_adenocarcinoma.html",
        "large cell carcinoma": "diagnosis/know_more_largecell.html",
        "squamous cell carcinoma": "diagnosis/know_more_squamous.html",
    }
    template = template_map.get(diagnosis.lower())
    if template:
        return render(request, template)
    return redirect('home')

# --- Load model + metadata once ---
model_path = os.path.join(settings.BASE_DIR, 'diagnosis', 'chest_ct_model.h5')
meta_path = os.path.join(settings.BASE_DIR, 'diagnosis', 'model_metadata.joblib')

model = tf.keras.models.load_model(model_path)
meta = joblib.load(meta_path)

class_labels = meta['class_labels']
if isinstance(class_labels, dict):
    class_labels = [class_labels[i] for i in sorted(class_labels.keys())]

last_conv_layer_name = meta.get('last_conv_layer_name', 'block5_conv3')
img_size = meta['img_shape']

# --- CT Upload + Prediction ---
def upload_ct(request):
    if request.method == 'POST' and request.FILES.get('ct_image'):
        ct_file = request.FILES['ct_image']

        # Ensure media directory exists
        media_dir = os.path.join(settings.BASE_DIR, "media")
        os.makedirs(media_dir, exist_ok=True)

        # Save uploaded file
        upload_path = os.path.join(media_dir, f"uploaded_{ct_file.name}")
        with open(upload_path, 'wb+') as destination:
            for chunk in ct_file.chunks():
                destination.write(chunk)

        # Preprocess
        img_raw = Image.open(upload_path).convert("RGB").resize(img_size)
        img_array = np.array(img_raw)
        img_batch = np.expand_dims(img_array, axis=0)
        img_preprocessed = preprocess_input(img_batch.astype(np.float32))

        # Prediction
        preds = model.predict(img_preprocessed)
        pred_index = np.argmax(preds[0])
        pred_label = class_labels[pred_index]
        confidence = float(preds[0][pred_index])

        # Normalize prediction string
        normalized_label = pred_label.strip().lower().replace(".", "").replace(" ", "")

        # Map prediction to static heatmap
        heatmap_map = {
            "normal": "heatmaps/normal.png",
            "adenocarcinoma": "heatmaps/adenocarcinoma.png",
            "largecellcarcinoma": "heatmaps/largecell.png",
            "squamouscellcarcinoma": "heatmaps/squamous.png",
        }
        heatmap_path = heatmap_map.get(normalized_label, None)

        return render(request, 'diagnosis/result.html', {
            'prediction': pred_label,
            'confidence': confidence,
            'uploaded_image_url': f"uploaded_{ct_file.name}",  # relative to MEDIA_URL
            'heatmap_path': heatmap_path,
            'patient_id': request.POST.get('patient_id'),
            'name': request.POST.get('name'),
            'age': request.POST.get('age'),
            'gender': request.POST.get('gender'),
        })
    return render(request, 'diagnosis/patient_form.html')