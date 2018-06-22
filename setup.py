from setuptools import find_packages, setup

setup(
    name='metaform',
    version='0.0.2',
    description='A utility for defining metadata for data types and formats.',
    url='https://github.com/mindey/metaform',
    author='Mindey',
    author_email='mindey@qq.com',
    license='AGPL',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires=["boltons", "python-slugify"],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    zip_safe=False
)

