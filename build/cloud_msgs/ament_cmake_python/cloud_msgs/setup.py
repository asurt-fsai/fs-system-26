from setuptools import find_packages
from setuptools import setup

setup(
    name='cloud_msgs',
    version='1.0.0',
    packages=find_packages(
        include=('cloud_msgs', 'cloud_msgs.*')),
)
