#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="monocleaner",
    version="1.2",
    license="GNU General Public License v3.0",
    author="Prompsit Language Engineering",
    author_email="info@prompsit.com",
    maintainer="Jaume Zaragoza",
    maintainer_email="jzaragoza@prompsit.com",
    description="Monolingual corpus fluency filter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bitextor/monocleaner",
    packages=setuptools.find_packages(),
    install_requires=[
        "regex",
        "toolwrapper",
        "sacremoses",
        "numpy",
        "pyyaml",
        "fastspell==0.8",
    ],
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters"
    ],
    project_urls={
        "Monocleaner on GitHub": "https://github.com/bitextor/monocleaner",
        "Prompsit Language Engineering": "http://www.prompsit.com",
        "Macocu": "https://macocu.eu/"
    },
    scripts=[
        "scripts/monocleaner",
        "scripts/monocleaner-train",
        "scripts/monocleaner-download",
    ]
)
