import os
import setuptools
import shutil

from mccole import __version__ as version

if not os.path.exists("mccole/data"):
    os.mkdir("mccole/data")
shutil.make_archive("mccole/data/mccole", "zip", "data")

setuptools.setup(
    name="mccole",
    version=version,
    url="https://github.com/gvwilson/mccole",
    author="Greg Wilson",
    author_email="gvwilson@third-bit.com",
    description="A book theme for Ivy",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["*test*"]),
    include_package_data=True,
    scripts=["bin/mccole"],
    install_requires=[
        "beautifulsoup4>=4.11",
        "html5validator>=0.4.0",
        "ivy>=6.4",
        "pybtex>=0.24",
        "pymdown-extensions>=9.3",
    ],
    package_data={"": ["mccole/data/mccole.zip"]},
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
)
