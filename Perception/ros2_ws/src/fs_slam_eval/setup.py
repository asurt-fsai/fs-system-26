import os
from glob import glob
from setuptools import setup

package_name = 'fs_slam_eval'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # --- ADD THESE LINES TO INSTALL LAUNCH & CONFIG FILES ---
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # --------------------------------------------------------
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='eyad',
    maintainer_email='eyad@todo.todo',
    description='Benchmarking ZED SLAM vs RTAB-Map',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "test_node = fs_slam_eval.my_node:main"
        ],
    },
)