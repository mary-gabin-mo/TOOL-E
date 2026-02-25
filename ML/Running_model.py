# Libraries
import torch
import torch.nn as nn
from torchvision import transforms, models
from torchvision.models import EfficientNet_V2_S_Weights
from PIL import Image



# ==========================================
# CONFIGURATION
# ==========================================
IMAGE_PATH = 'test (6).jpg'        # The image you want to classify
MODEL_PATH = 'efficientnet_finetuned_sprint2.pth' # Path to one of your saved models

# IMPORTANT: These must match the folder names in your dataset EXACTLY,
# and be in alphabetical order (0, 1, 2...).
CLASS_NAMES = ['adjustable_wrench', 'allen_key', 'box_cutter', 'breadboard', 'caliper', 'channel_lock', 'file', 'hot_glue_gun', 'multimeter', 'plier', 'safety_glasses', 'scissors', 'screwdriver', 'super_glue', 'tape_measure']
#CLASS_NAMES = ['adjustable_wrench', 'box_cutter']

# EfficientNet V2 S Stats
IMG_SIZE = 384
NORMALIZE_MEAN = [0.485, 0.456, 0.406]
NORMALIZE_STD = [0.229, 0.224, 0.225]

# ==========================================
# SETUP
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define the Transform (Same as the "Clean" validation transform)
inference_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD)
])

def load_model(path, num_classes):
    print("Building model architecture...")
    # Load the base architecture
    weights = EfficientNet_V2_S_Weights.DEFAULT
    model = models.efficientnet_v2_s(weights=weights)

    # Re-create the modified head (Vital step!)
    # The saved file only has numbers (weights), not the structure.
    # We must rebuild the structure exactly as it was during training.
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    # Load the weights
    print(f"Loading weights from {path}...")
    # map_location ensures this runs even if you trained on GPU but test on CPU
    model.load_state_dict(torch.load(path, map_location=device))

    model.to(device)
    model.eval() # Set to evaluation mode (Freezes Dropout/Batch Norm)
    return model

# ==========================================
# RUN PREDICTION
# ==========================================
if __name__ == '__main__':
    try:
        # Load Model
        model = load_model(MODEL_PATH, len(CLASS_NAMES))

        # Load and Preprocess Image
        image = Image.open(IMAGE_PATH).convert('RGB') # Ensure it's RGB
        input_tensor = inference_transform(image)

        # Add batch dimension (Model expects [1, 3, 384, 384], not [3, 384, 384])
        input_batch = input_tensor.unsqueeze(0).to(device)

        # Predict
        with torch.no_grad():
            output = model(input_batch)

            # Convert raw output to probabilities
            probabilities = torch.nn.functional.softmax(output[0], dim=0)

            # Get top prediction
            top_prob, top_catid = torch.topk(probabilities, 1)

            # Map ID to Name
            class_id = top_catid.item()
            score = top_prob.item()
            class_name = CLASS_NAMES[class_id]

            print(f"\n-----------------------------")
            print(f"Prediction: {class_name.upper()}")
            print(f"Confidence: {score*100:.2f}%")
            print(f"-----------------------------")

            # Print all probabilities
            for i, prob in enumerate(probabilities):
                print(f"{CLASS_NAMES[i]}: {prob.item()*100:.2f}%")

    except FileNotFoundError:
        print(f"Error: File not found. Check {IMAGE_PATH} or {MODEL_PATH}")
    except Exception as e:
        print(f"An error occurred: {e}")