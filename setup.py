import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scubot-tags",
    version="2.0.0.dev0",
    author="Scubot Team",
    description="Tagging system for Scubot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scubot/tags",
    packages=setuptools.find_packages(),
    install_requires=[
        "tinydb",
        "discord",

        "reaction-scroll @ git+https://github.com/scubot/reaction-scroll.git"
        "@prototype"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)