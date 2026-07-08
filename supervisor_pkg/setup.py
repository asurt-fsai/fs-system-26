import os
from importlib_metadata import entry_points
from setuptools import find_packages, setup
from glob import glob

package_name = 'supervisor_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join('share', package_name, 'json'), glob('json/*.json')),
        (os.path.join('share', package_name, 'assests'), glob('assests/*')),
],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yasmeentamer',
    maintainer_email='yasmeentamer@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],

        entry_points={
    'console_scripts': [

        # =========================
        # CORE SYSTEM
        # =========================
        "supervisor_node = supervisor.helpers.Supervisor:main",
        "mission_manager_node = supervisor.nodes.mission_manager_node:main",
        "module_manager_node = supervisor.nodes.module_manager_node:main",
        "mission_node = supervisor.nodes.mission_node:main",
        "interface = supervisor.helpers.GUI.main_gui:main",
        "status = supervisor.helpers.GUI.status_gui:main",
        "static_mission_gui = supervisor.helpers.GUI.static_mission_gui:main",

        # =========================
        # GUI TEST / DEV STATES
        # =========================
        "testgui = supervisor.helpers.GUI.MYstateMachine:main",
        "testModule = supervisor.helpers.GUI.statemachine:main",
        "state_machine_gui = supervisor.helpers.GUI.MYstateMachine:main",

        # =========================
        # MISSIONS
        # =========================
        "autoDemo = supervisor.helpers.Missions.AutoDemoMission:main",
        "staticA = supervisor.helpers.Missions.StaticAMission:main",
        "staticB = supervisor.helpers.Missions.StaticBMission:main",
        "skidpad = supervisor.helpers.Missions.SkidpadMission:main",
        "trackdrive = supervisor.helpers.Missions.TrackdriveMission:main",
        "acceleration = supervisor.helpers.Missions.AccelerationMission:main",
        "autocross = supervisor.helpers.Missions.AutocrossMission:main",

        # =========================
        # MODULE / SYSTEM HELPERS
        # =========================
        "missionLauncher = supervisor.helpers.Module.MissionLauncher:main",
        "mission_finisher = supervisor.helpers.Module.MissionFinisher:main",
        "odom_tracker = supervisor.helpers.Module.odom_tracker:main",

        # =========================
        # COMMANDS (if executable nodes exist)
        # =========================
        "emergency_stop = supervisor.helpers.Commands.EmergencyStopCommand:main",
        "restart_module = supervisor.helpers.Commands.RestartModuleCommand:main",
        "shutdown_modules = supervisor.helpers.Commands.ShutdownModulesCommand:main",
        "start_mission = supervisor.helpers.Commands.StartMissionCommand:main",

        # =========================
        # COMMUNICATION
        # =========================
        "vcu_simulator = supervisor.nodes.vcu_simulator:main",


    ],
}

)
