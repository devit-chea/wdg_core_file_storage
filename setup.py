from setuptools import setup, find_packages
from wdg_file_storage import __version__

setup(
    name="wdg-file-storage",
    version=__version__,    
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=3.8",
        "boto3",
        "django-storages",
    ],
    description="Reusable DRF package for X functionality",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="storage service s3",
    url="https://github.com/devit-chea/drf-file-storage",
    author="DC CD",
    author_email="you@dccd.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "License :: OSI Approved :: MIT License",
    ],
)
