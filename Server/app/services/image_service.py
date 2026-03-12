import os
import uuid
import time
import shutil

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAPTURED_IMAGES_DIR = os.path.join(BASE_DIR, 'captured_images')
TEMP_IMAGES_DIR = os.path.join(CAPTURED_IMAGES_DIR, 'temp')

def init_image_dirs():
    os.makedirs(TEMP_IMAGES_DIR, exist_ok=True)

def save_temp_image(contents: bytes, filename: str = None) -> str:
    # 1. Generate a Unique ID (Timestamp + Random)
    unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"

    if not filename or filename == "capture.jpg":
        filename = f"{unique_id}.jpg"
    else:
        # Keep original name but append ID to prevent overwrites if two people use the kiosk at the exact same millisecond
        name, ext = os.path.splitext(os.path.basename(filename))
        filename = f"{name}_{unique_id}{ext}"
    
    # Ensure secure filename just in case
    filename = os.path.basename(filename)
    
    temp_path = os.path.join(TEMP_IMAGES_DIR, filename)
    with open(temp_path, "wb") as f:
        f.write(contents)
    return filename

def get_temp_image_path(filename: str) -> str:
    return os.path.join(TEMP_IMAGES_DIR, filename)

def move_image_to_permanent(filename: str, tool_name: str, classification_correct: bool, new_transaction_id: str = None) -> str:
    """
    Moves image from temp to permanent storage.
    If new_transaction_id is provided, the file will be renamed to match it.
    Returns the final filename.
    """
    temp_path = get_temp_image_path(filename)
    if not os.path.exists(temp_path):
        return None
        
    # Sanitize tool name
    safe_tool_name = "".join([c for c in tool_name if c.isalnum() or c in (' ', '-', '_')]).strip()
    
    # Target structure: captured_images/Yes/ToolName/file.jpg
    base_target_dir = os.path.join(CAPTURED_IMAGES_DIR, 'Yes' if classification_correct else 'No')
    tool_target_dir = os.path.join(base_target_dir, safe_tool_name)
    os.makedirs(tool_target_dir, exist_ok=True)
    
    # Rename the file if requested, otherwise keep original
    if new_transaction_id:
        ext = os.path.splitext(filename)[1] or '.jpg'
        new_filename = f"{new_transaction_id}{ext}"
    else:
        new_filename = filename
        
    target_path = os.path.join(tool_target_dir, new_filename)
    
    shutil.move(temp_path, target_path)
    
    # Return just the image name instead of the full relative path
    return new_filename

def cleanup_temp_files(max_age_hours=24):
    """Deletes files in temp directory older than max_age_hours"""
    print("[SERVER] Running cleanup of old temp images...")
    now = time.time()
    count = 0
    if os.path.exists(TEMP_IMAGES_DIR):
        for filename in os.listdir(TEMP_IMAGES_DIR):
            file_path = os.path.join(TEMP_IMAGES_DIR, filename)
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > (max_age_hours * 3600):
                    try:
                        os.remove(file_path)
                        count += 1
                    except Exception as e:
                        print(f"[SERVER] Error deleting {filename}: {e}")
    if count > 0:
        print(f"[SERVER] Cleaned up {count} old temp images.")
