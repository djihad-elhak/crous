import os
from datetime import datetime


def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def screenshot_filename(directory: str = "screenshots") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(directory, f"listing_{timestamp}.png")
