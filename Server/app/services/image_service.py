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

def save_temp_image(contents: bytes) -> str:
    filename = f"{uuid.uuid4()}.jpg"
    temp_path = os.path.join(TEMP_IMAGES_DIR, filename)
    with open(temp_path, "wb") as f:
        f.write(contents)
    return filename

def get_temp_image_path(filename: str) -> str:
    return os.path.join(TEMP_IMAGES_DIR, filename)

def move_image_to_permanent(filename: str, tool_name: str, classification_correct: bool) -> str:
    """
    Moves image from temp to permanent storage.
    Returns the relative path from BASE_DIR.
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
    
    new_filename = f"{safe_tool_name}_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
    target_path = os.path.join(tool_target_dir, new_filename)
    
    shutil.move(temp_path, target_path)
    
    return os.path.relpath(target_path, BASE_DIR)

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
