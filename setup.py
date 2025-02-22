from setuptools import setup, find_packages
from wdg_core_file_storage import __version__


setup(
    name="wdg-core-file-storage",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=4.2",
        "boto3>=1.36",
        "django-storages>=1.14",
    ],
    python_requires=">=3.9",
    description="Support for s3 storage backends in Django",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="storage service s3",
    url="https://github.com/devit-chea/wdg_core_file_storage",
    author="Devit Chea",
    author_email="devit.chea1998@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
