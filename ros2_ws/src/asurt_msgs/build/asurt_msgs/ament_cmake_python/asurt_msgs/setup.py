from setuptools import find_packages
from setuptools import setup

setup(
    name='asurt_msgs',
    version='2.0.0',
    packages=find_packages(
        include=('asurt_msgs', 'asurt_msgs.*')),
)
