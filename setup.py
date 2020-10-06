import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name='kraky',
    version='0.1.5',
    description='Python asyncio client for Kraken API REST and Kraken Websockets API using httpx and websockets',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Kevin Messer',
    author_email='contact@kevin-messer.net',
    url='https://github.com/Atem18/kraky',
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    install_requires=[
        "httpx",
        "websockets",
    ],
)
