from setuptools import setup, find_packages

setup(
    name="rockphysics",
    version="0.1.0",
    author="Jeffrey Roth",
    author_email="jeff.roth@thinkonward.com",
    description="A Python package for rock physics calculations and analysis.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    package_data={
        'rockphysics': ['resources/*.yaml'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.8',
    install_requires=[
        'pandas',
        'numpy',
        'matplotlib',
        'pyyaml',
        'scipy',
        'lasio',
        'pint',
        'ipywidgets',
    ],
)