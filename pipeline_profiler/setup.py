from setuptools import find_packages, setup

package_name = 'pipeline_profiler'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='eyad',
    maintainer_email='eyadahmedhabib2007@gmail.com',
    description='ROS 2 node that monitors and prints pipeline computation times.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pipeline_profiler = pipeline_profiler.profiler:main',
        ],
    },
)
