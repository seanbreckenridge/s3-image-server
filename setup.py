from pathlib import Path
from setuptools import setup, find_packages

requirements = Path("lib_requirements.txt").read_text().splitlines()

pkg = "s3_image_uploader"
setup(
    name=pkg,
    version="0.0.1",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description="upload to the s3 bucket",
    packages=find_packages(include=[pkg]),
    package_data={pkg: ["py.typed"]},
    install_requires=requirements,
    python_requires=">=3.8",
    extras_require={
        "testing": [
            "pytest",
            "mypy",
            "flake8",
        ],
    },
    entry_points={"console_scripts": ["{pkg} = {pkg}.__main__:main".format(pkg=pkg)]},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
