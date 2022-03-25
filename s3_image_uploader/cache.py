"""
simple cache uses a local dir to mirror the state remotely (saving empty files)
so we can check if we've uploaded it before
"""

import os
from pathlib import Path

DEFAULT_DATA_DIR = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
DEFAULT_S3_INDEX = os.path.join(DEFAULT_DATA_DIR, "s3_img_cache")
CACHE_DIR = os.environ.get("S3_IMAGE_UPLOAD_INDEX", DEFAULT_S3_INDEX)


def has(path: str) -> bool:
    """
    e.g. pass in 'foo.jpg'
    if it exists in the cache dir, that means
    we've uploaded it to s3 already
    """
    return os.path.exists(os.path.join(CACHE_DIR, path))


def add(path: str) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    Path(os.path.join(CACHE_DIR, path)).touch()
