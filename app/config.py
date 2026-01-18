import os

# Base directory for the application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define paths for persistent data
# If running on Render with a persistent disk, these env vars should be set.
# Otherwise, default to local development paths.

# Text Files
# Default: data/texts
TEXTS_DIR = os.getenv("TEXTS_DIR", os.path.join(BASE_DIR, "data", "texts"))

# Audio Files
# Default: static/audio
AUDIO_DIR = os.getenv("AUDIO_DIR", os.path.join(BASE_DIR, "static", "audio"))

# Image Uploads
# Default: static/images/uploads
IMAGES_DIR = os.getenv("IMAGES_DIR", os.path.join(BASE_DIR, "static", "images", "uploads"))

# Ensure directories exist (safe to call repeatedly)
os.makedirs(TEXTS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
