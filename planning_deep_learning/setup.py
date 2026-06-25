from setuptools import find_packages, setup
import glob
import os

package_name = 'planning_deep_learning'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    package_data={package_name: ['Completed_Models/*']},
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/dl_node_launch.py']),
        (
            'share/' + package_name + '/Completed_Models',
            [p for p in glob.glob('planning_deep_learning/Completed_Models/*') if os.path.isfile(p)]
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='jumana.yasser777@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "dl_node = planning_deep_learning.node:main"
        ],
    },
)
