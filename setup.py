from setuptools import setup, find_packages
import os
from glob import glob

package_name = "planning_voronoi"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(),
    py_modules=["voronoi_node"],
    data_files=[
        # ROS2 package index
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        # Launch files
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        # Config / parameter files
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Karim",
    maintainer_email="TODO@todo.com",
    description="Voronoi-based path planning for Formula Student",
    license="TODO",
    entry_points={
        "console_scripts": [
            "voronoi_node = voronoi_node:main",
        ],
    },
)
