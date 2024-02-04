
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='streamlit_stacker',
    version='0.0.5',
    author="Baptiste Ferrand",
    author_email="bferrand.maths@gmail.com",
    description="Tool allowing to stack streamlit commands and resolve them in a controlable manner.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/B4PT0R/streamlit_stacker",
    packages=find_packages(),
    package_data={
        'streamlit_stacker': ['components.json'],
    },
    # Specify the dependencies
    install_requires=[
        'streamlit>=1.30.0',
        'streamlit_modal_input',
        'streamlit_pdf_reader'
    ],
)
