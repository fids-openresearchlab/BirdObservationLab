import os
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent

def get_work_dir() -> Path:
    return Path(os.getcwd())
