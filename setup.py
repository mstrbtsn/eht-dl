from setuptools import setup, find_packages
with open('requirements.txt') as requirements_file:
    install_requirements = requirements_file.read().splitlines()

setup(
    name="eht_dl",
    version="0.3.0",
    description="eht-dl",
    author="mstrbtsn",
    packages=find_packages(),
    install_requires=install_requirements,
    entry_points={
        "console_scripts": [
            "eht-dl=eht_dl.__main__:main",
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3.10.6',
    ]
)
