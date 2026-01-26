# gepro/__init__.py
# Modular GIS Processing Library

from .core import execute_workflow, run_from_file
from .utils import load_chunks, save_chunks, run_cleaning_pipeline
from .script_generator import generate_python_script

__version__ = "1.0.0"
__all__ = [
    "execute_workflow", 
    "run_from_file", 
    "generate_python_script",
    "load_chunks",
    "save_chunks",
    "run_cleaning_pipeline"
]

