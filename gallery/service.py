import os
import uuid

def hash_upload_path(instance: object, filename: str) -> str:
    """Generate a random hash filename while preserving the extension."""
    ext = os.path.splitext(filename)[1]  # Get the file extension
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('pictures/', random_filename)

def miniature_upload_path(instance: object, filename: str) -> str:
    """Generate a random hash filename for miniatures while preserving the extension."""
    ext = os.path.splitext(filename)[1]  # Get the file extension
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('miniatures/', random_filename)