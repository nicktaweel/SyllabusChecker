from setuptools import setup, find_packages
import glob
import os

# Find all .py files in src (excluding __init__.py if present)
module_files = glob.glob("src/*.py")
module_names = [os.path.splitext(os.path.basename(f))[0] for f in module_files]

setup(
    name="SyllabusCheckerForPy",
    version="1.0.0",
    description="A program that allows the user to input and analyze syllabi",
    author="",  # optional
    author_email="",  # optional
    license="MIT",

    # Modules instead of packages
    py_modules=module_names,
    package_dir={"": "src"},

    python_requires=">=3.8",

    install_requires=[
        "pillow",
        "reportlab",
        "pypdf",
        "sentence-transformers",
        "numpy",
        "textstat"
    ],

    include_package_data=True,

    entry_points={
        "console_scripts": [
            # Example if you want a command:
            # "syllcheck = main:main",
        ]
    },
)
