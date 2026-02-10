from setuptools import setup
import os
from glob import glob

package_name = 'cone_mapping'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ASU Racing SLAM Team',
    maintainer_email='slam@asu-racing.com',
    description='Cone mapping and localization for Formula Student Driverless',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'cone_mapping_node = cone_mapping.cone_mapping_node:main',
            'message_adapter = cone_mapping.message_adapter:main',
            'pose_republisher = cone_mapping.pose_republisher:main',
        ],
    },
)
