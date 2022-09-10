import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="argparse-director",
    version="0.4.3",
    author="Seth Neiman",
    author_email="seth@duckpapa.com",
    description="Simpler, yet powerful drop-in replacement for argparser adding configuration files containing executable code, hidden and grouped arguments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sneiman/argparse_director",
    # packages=setuptools.find_packages(),
    py_modules = ['argparse_director'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

