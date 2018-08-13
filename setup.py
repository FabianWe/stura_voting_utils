import os
from setuptools import setup, find_packages
from stura_voting_utils import __version__


setup(
    name='stura_voting_utils',
    version=__version__,
    description='Utils for Schulze and Median voting as used by the student council Freiburg',
    url='https://github.com/FabianWe/stura_voting_utils',
    author='Fabian Wenzelmann',
    author_email='fabianwen@posteo.eu',
    license='MIT',
    keywords='voting schulze median',
    packages=find_packages(exclude=('docs', 'tests', 'env')),
    include_package_data=True,
    install_requires=['pytest'],
)
