import os
from setuptools import setup, find_packages

this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, "README.md"), "r") as f:
    long_description = f.read()

setup(
    name="flasynk",
    version=open("flasynk/version.py").readlines()[-1].split()[-1].strip("\"'"),
    description="Exposing Asynchronous endpoint using Flask-RestPlus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["test"]),
    install_requires=[
        # Used to manage endpoints and open api definition
        "flask-restplus==0.13.0"
    ],
    extras_require={
        "celery": ["celery[redis,msgpack]==4.3.0"],
        "huey": ["huey==2.1.1", "redis==3.3.8"],
        "testing": [
            # Extra requirements
            "celery[redis,msgpack]==4.3.0",
            "huey==2.1.1",
            # Used to manage testing of a Flask application
            "pytest-flask==0.15.0",
        ],
    },
    python_requires=">=3.6",
    project_urls={
        "Changelog": "https://github.tools.digital.engie.com/GEM-Py/flasynk/blob/master/CHANGELOG.md",
        "Issues": "https://github.tools.digital.engie.com/GEM-Py/flasynk/issues",
    },
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
        "Topic :: Software Development :: Build Tools",
    ],
    keywords=["async", "asynchronous", "rest", "flask"],
    platforms=["Windows", "Linux"],
)
