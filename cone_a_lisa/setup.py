import os
from glob import glob
from setuptools import setup

package_name = 'cone_a_lisa'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Add this line to install the launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=[
    'setuptools',
    'geometry_msgs',
    'nav_msgs',
    'tf2_ros',
    'tf2_geometry_msgs',
    ],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='Cone-a Lisa package',
    license='Your License',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'cone_a_lisa = cone_a_lisa.cone_a_lisa:main',
            'landmark_to_marker = cone_a_lisa.landmark_to_marker:main',
            'map_plot = cone_a_lisa.map_plot:main',
        ],
    },
)
