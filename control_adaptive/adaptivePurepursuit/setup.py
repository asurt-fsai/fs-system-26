"""setup file for the adaptive_pure_pursuit package"""
from glob import glob
import os
from setuptools import find_packages, setup

PACKAGENAME = "adaptive_pure_pursuit"

setup(
    name=PACKAGENAME,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGENAME]),
        ("share/" + PACKAGENAME, ["package.xml"]),
        (os.path.join("share", PACKAGENAME, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", PACKAGENAME, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="marwanmahmoud",
    maintainer_email="mohammed.alaa200080@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "adaptive_pp_node = adaptive_purepursuit.adaptive_pp_node:main",
            "adaptive_pp_visualizer = adaptive_purepursuit.adaptive_pp_visualizer:main" 
        ],
    },
)
