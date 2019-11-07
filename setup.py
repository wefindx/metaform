# Copyright (c) 2018 WeFindX Foundation, CLG.
# All Rights Reserved.

from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    long_description = f.read()


setup(
    name='metaform',
    version='1.0.1.3',
    description='A utility for defining metadata for data types and formats.',
    long_description=long_description,
    url='https://gitlab.com/wefindx/metaform',
    author='Mindey',
    author_email='mindey@qq.com',
    license='ASK FOR PERMISSIONS',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        "metawiki",
        "typology",
        "metadir",
        "tinydb",
        "python-dateutil",
    ],
    extras_require={
        'develop': [
            'pre-commit==1.18.3',
            'coverage==4.5.4',
            'flake8==3.7.8',
            'isort==4.3.21',
        ],
    },
    zip_safe=False
)
