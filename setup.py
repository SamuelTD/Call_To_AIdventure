from setuptools import setup, find_packages

setup(
    name="myproject",            # replace with your project’s name
    version="0.1.0",
    author="Samuel Thorez-Debrucq",
    author_email="s.thorez@hotmail.fr",
    description="",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/SamuelTD/Call_To_AIdventure",  # optional
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "chromadb",
        "langchain",
        "langchain-community",
        "langchain-core",
        "langchain-ollama"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",      # or your license
        "Operating System :: OS Independent",
    ],
)
