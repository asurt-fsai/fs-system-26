data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/supervisor']),
    ('share/supervisor', ['package.xml']),
    ('share/supervisor/launch', ['launch/supervisor.launch.py']),
],
entry_points={
    'console_scripts': [
        'Supervisor = supervisor.Supervisor:main',
        'CommunicationLayer = supervisor.CommunicationLayer:main',
    ],
},