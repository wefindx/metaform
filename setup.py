# Copyright (c) 2018 WeFindX Foundation, CLG.
# All Rights Reserved.

from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='metaform',
    version='0.7.2',
    description='A utility for defining metadata for data types and formats.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/wefindx/metaform',
    author='Mindey',
    author_email='mindey@qq.com',
    license='ASK FOR PERMISSIONS',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        "metawiki",
        "metadir",
        "metadrive",
        "python-dateutil",
        "typology",
        "python-slugify",
        "tinydb",
        "boltons",
        "yolk3k",
        "click",
        "pymongo"
    ],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    zip_safe=False,
    entry_points = {
        'console_scripts': [
            'harvest=metaform.cli:harvest',
        ],
    }
)
