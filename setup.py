from setuptools import setup, find_packages

setup(
    name="rockphysics",
    version="0.1.0",  # Replace with your actual version
    packages=find_packages(),
    install_requires=[
        "pandas",
        "lasio",
        "pint",
        "matplotlib",
        "scipy"
    ],
    # Add other metadata like description, author, license, etc.
)