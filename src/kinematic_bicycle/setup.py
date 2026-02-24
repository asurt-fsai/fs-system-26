from setuptools import find_packages, setup
import os  
from glob import glob

package_name = 'kinematic_bicycle'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share', package_name), glob('launch/*.rviz'))  

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='amin',
    maintainer_email='amin@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'kinematic_bicycle = kinematic_bicycle.main:main',
            'path_gen = kinematic_bicycle.path_gen:main',
            #'test = kinematic_bicycle.controller:main',
            'controller = kinematic_bicycle.controller:main',
            #'live_plotter = telemetry_dashboard.live_plotter:main',
        ],
    },
)
