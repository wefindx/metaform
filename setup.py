from setuptools import find_packages, setup

setup(
    name='metaform',
    version='0.0.6',
    description='A utility for defining metadata for data types and formats.',
    url='https://gitlab.com/wefindx/metaform',
    author='Mindey',
    author_email='mindey@qq.com',
    license='ASK FOR PERMISSIONS',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires=["boltons", "python-slugify"],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    zip_safe=False
)

