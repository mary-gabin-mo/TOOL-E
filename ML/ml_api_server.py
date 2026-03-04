
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch
import torch.nn as nn
from torchvision import transforms, models
from torchvision.models import EfficientNet_V2_S_Weights
from PIL import Image
import io
import os
import json

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_PATH = 'efficientnet_finetuned_sprint2.pth' 
CLASS_NAMES_PATH = 'class_names.json'

# Load Class Names
try:
    with open(CLASS_NAMES_PATH, 'r') as f:
        CLASS_NAMES = json.load(f)
except FileNotFoundError:
    print(f"Error: {CLASS_NAMES_PATH} not found. Please ensure the file exists.")
    CLASS_NAMES = []
except json.JSONDecodeError:
    print(f"Error: Failed to decode {CLASS_NAMES_PATH}.")
    CLASS_NAMES = []

# EfficientNet V2 S Stats
IMG_SIZE = 384
NORMALIZE_MEAN = [0.485, 0.456, 0.406]
NORMALIZE_STD = [0.229, 0.224, 0.225]

# ==========================================
# SETUP MODEL AND TRANSFORM
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define the Transform 
inference_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD)
])

def load_model(path, num_classes):
    print("Building model architecture...")
    weights = EfficientNet_V2_S_Weights.DEFAULT
    model = models.efficientnet_v2_s(weights=weights)

    # Re-create the modified head
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    # Load the weights
    print(f"Loading weights from {path}...")
    if os.path.exists(path):
        model.load_state_dict(torch.load(path, map_location=device))
    else:
        print(f"WARNING: Model file not found at {path}. Server handles requests but prediction will fail unless model is loaded.")

    model.to(device)
    model.eval() 
    return model

# Initialize model on startup
print("Initializing ML Model...")
model = None
if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH, len(CLASS_NAMES))
else:
    print(f"Error: Model path {MODEL_PATH} does not exist.")

# ==========================================
# API SETUP
# ==========================================
app = FastAPI(title="TOOL-E ML Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "running", "model_loaded": model is not None, "device": str(device)}

@app.post("/predict")
async def predict_tool(file: UploadFile = File(...)):
    """
    Receives an image file, processes it, and returns the predicted tool class and confidence score.
    """
    if model is None:
         raise HTTPException(status_code=503, detail="Model is not loaded properly.")
    
    try:
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # Preprocess
        input_tensor = inference_transform(image)
        input_batch = input_tensor.unsqueeze(0).to(device)

        # Predict
        with torch.no_grad():
            output = model(input_batch)
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            
            # Get top prediction
            top_prob, top_catid = torch.topk(probabilities, 1)
            class_id = top_catid.item()
            score = top_prob.item()
            class_name = CLASS_NAMES[class_id]
            
            # Get all probabilities for detailed response if needed
            all_probs = {CLASS_NAMES[i]: prob.item() for i, prob in enumerate(probabilities)}

        return {
            "success": True,
            "prediction": class_name,
            "confidence": score,
            "all_probabilities": all_probs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

if __name__ == '__main__':
    # Run on a different port than the main API server (e.g., 5001)
    uvicorn.run(app, host="0.0.0.0", port=5001)
