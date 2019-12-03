import os
from setuptools import setup, find_packages

this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, "README.md"), "r") as f:
    long_description = f.read()

setup(
    name="flasynk",
    version=open("flasynk/version.py").readlines()[-1].split()[-1].strip("\"'"),
    author="Colin Bounouar",
    author_email="colin.bounouar.dev@gmail.com",
    maintainer="Colin Bounouar",
    maintainer_email="colin.bounouar.dev@gmail.com",
    url="https://colin-b.github.io/flasynk/",
    description="Exposing Asynchronous endpoint using Flask-RestPlus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    download_url="https://pypi.org/project/flasynk/",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Build Tools",
    ],
    keywords=["async", "asynchronous", "rest", "flask"],
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        # Used to manage endpoints and open api definition
        "flask-restplus==0.13.*"
    ],
    extras_require={
        "celery": ["celery[redis,msgpack]==4.*"],
        "huey": ["huey==2.*", "redis==3.*"],
        "testing": [
            # Extra requirements
            "celery[redis,msgpack]==4.*",
            "huey==2.*",
            # Used to manage testing of a Flask application
            "pytest-flask==0.15.*",
            # Used to check coverage
            "pytest-cov==2.*",
        ],
    },
    python_requires=">=3.6",
    project_urls={
        "GitHub": "https://github.com/Colin-b/flasynk",
        "Changelog": "https://github.com/Colin-b/flasynk/blob/master/CHANGELOG.md",
        "Issues": "https://github.com/Colin-b/flasynk/issues",
    },
    platforms=["Windows", "Linux"],
)
