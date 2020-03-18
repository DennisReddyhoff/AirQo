import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="get_dataframe", # Replace with your own username
    version="0.0.1",
    author="Dennis Reddyhoff",
    author_email="d.reddyhoff@sheffield.ac.uk",
    description="Package to pull down and cache data from AirQo sensor APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DennisReddyhoff/AirQo",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)