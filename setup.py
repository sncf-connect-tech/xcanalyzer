import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xcanalyzer",
    version="0.0.1",
    author="Ghislain Deffrasnes",
    author_email="gdeffrasnes@oui.sncf",
    description="A project that aims to make static analysis on a Xcode project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/voyages-sncf-technologies/xcanalyzer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: BSD 3-Clause License :: E-Voyageurs Technologies",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'termcolor==1.1.0',
        'pbxproj==2.5.1',
    ],
)