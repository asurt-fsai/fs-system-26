import os
import sys
import json
import types
import pytest
import logging

# Provide lightweight stubs for ROS packages so imports don't fail during test collection
sys.modules.setdefault('rclpy', types.ModuleType('rclpy'))
sys.modules.setdefault('rclpy.node', types.ModuleType('rclpy.node'))
sys.modules.setdefault('rclpy.executors', types.ModuleType('rclpy.executors'))
setattr(sys.modules['rclpy.node'], 'Node', type('Node', (), {}))
setattr(sys.modules['rclpy.executors'], 'MultiThreadedExecutor', type('MultiThreadedExecutor', (), {}))
sys.modules.setdefault('std_msgs', types.ModuleType('std_msgs'))
sys.modules.setdefault('std_msgs.msg', types.ModuleType('std_msgs.msg'))
setattr(sys.modules['std_msgs.msg'], 'String', type('String', (), {}))

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

# Load MissionStatus directly (avoid package import ambiguity)
import importlib.util
ms_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'MissionStatus.py'))
spec2 = importlib.util.spec_from_file_location('mm_status', ms_path)
mm_status = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mm_status)
MissionStatus = mm_status.MissionStatus


def load_mission_manager_class(comm):
    """Dynamically load MissionManager from file into a controlled namespace.

    comm: communication stub instance to be returned by CommunicationLayer.getInstance()
    Returns the MissionManager class object loaded into a fresh namespace.
    """
    mm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'MissionManager.py'))
    with open(mm_path, 'r') as f:
        src = f.read()

    # Remove imports that would try to load heavy dependencies and rely on injected symbols
    # Strip any import that pulls from supervisor.helpers to avoid importing the real modules
    lines = []
    for ln in src.splitlines(True):
        if ln.strip().startswith('from supervisor.helpers'):
            continue
        lines.append(ln)
    src = ''.join(lines)

    ns = {}
    # Inject required symbols
    ns['Module'] = DummyModule
    ns['AccelerationMission'] = DummyMission
    ns['SkidpadMission'] = DummyMission
    ns['AutocrossMission'] = DummyMission
    ns['TrackdriveMission'] = DummyMission
    ns['MissionStatus'] = MissionStatus
    # CommunicationLayer must provide getInstance() -> comm
    ns['CommunicationLayer'] = type('C', (), {'getInstance': staticmethod(lambda: comm)})

    exec(compile(src, mm_path, 'exec'), ns)
    return ns['MissionManager']


class DummyMission:
    def __init__(self):
        self.missionStatus = None


class DummyModule:
    def __init__(self, pkg=None, launchFile=None, heartbeatTopic=None, isNodeMsg=None):
        self.pkg = pkg
        self.launchFile = launchFile
        self.heartbeatTopic = heartbeatTopic
        self.isNodeMsg = isNodeMsg


class CommStub:
    def __init__(self):
        self.registered = []

    def registerMission(self, mission):
        self.registered.append(mission)

    def registerModule(self, module):
        # used by some Module constructors; noop here
        pass


class ModuleManagerStub:
    def __init__(self, launch_result=None):
        self.registered_modules = None
        self.launch_result = launch_result if launch_result is not None else []
        self.shutdown_called = False

    def registerModules(self, modules):
        self.registered_modules = list(modules)

    def launchAll(self):
        return self.launch_result

    def shutdownAll(self):
        self.shutdown_called = True
        return []


@pytest.fixture(autouse=True)
def reset_singletons():
    # No-op fixture placeholder (we load MissionManager into fresh namespaces)
    yield


def write_mission_json(tmp_path, mission_type, modules):
    missions_dir = tmp_path / "missions"
    missions_dir.mkdir()
    path = missions_dir / f"{mission_type}.json"
    data = {"modules": modules}
    path.write_text(json.dumps(data))
    return str(missions_dir)


def test_start_mission_resolves_modules_and_sets_running(tmp_path, monkeypatch, caplog):
    # Prepare missions file
    modules_data = [
        {"pkg": "pkg_a", "launch_file": "a.launch", "heartbeats_topic": "hb/a", "is_node_msg": True},
        {"pkg": "pkg_b", "launch_file": "b.launch", "heartbeats_topic": "hb/b", "is_node_msg": False},
    ]
    write_mission_json(tmp_path, "acceleration", modules_data)

    # Change cwd so MissionManager.resolveModules finds missions/<type>.json
    monkeypatch.chdir(tmp_path)

    # Patch CommunicationLayer and Module used by MissionManager via dynamic loader
    comm = CommStub()
    mm_cls = load_mission_manager_class(comm)

    # Use Dummy mission factory that creates simple mission instances
    manager = mm_cls()
    mm_cls._instance = manager
    manager.missionFactory = {"acceleration": DummyMission}

    mm = ModuleManagerStub(launch_result=[])
    manager.setModuleManager(mm)

    # Capture logs
    caplog.set_level(logging.INFO)

    # Run
    manager.startMission("acceleration")

    # Assertions
    active = manager.getActiveMission()
    assert active is not None
    assert active.missionStatus == MissionStatus.RUNNING
    assert mm.registered_modules is not None
    assert len(mm.registered_modules) == 2
    # CommunicationLayer should have been registered with the mission on create
    assert len(comm.registered) >= 1
    assert comm.registered[0] is active
    # Log assertions
    messages = [r.message for r in caplog.records]
    assert any("Created mission" in m for m in messages)
    assert any("Loaded 2 modules for acceleration" in m for m in messages)
    assert any("Mission RUNNING" in m for m in messages)


def test_start_mission_fails_when_launch_fails(tmp_path, monkeypatch, caplog):
    modules_data = [
        {"pkg": "pkg_a", "launch_file": "a.launch", "heartbeats_topic": "hb/a", "is_node_msg": True}
    ]
    write_mission_json(tmp_path, "acceleration", modules_data)
    monkeypatch.chdir(tmp_path)

    comm = CommStub()
    mm_cls = load_mission_manager_class(comm)
    manager = mm_cls()
    mm_cls._instance = manager
    manager.missionFactory = {"acceleration": DummyMission}

    # Simulate failed launches by returning a non-empty list
    mm = ModuleManagerStub(launch_result=[1])
    manager.setModuleManager(mm)

    caplog.set_level(logging.INFO)
    manager.startMission("acceleration")

    active = manager.getActiveMission()
    assert active is not None
    assert active.missionStatus == MissionStatus.FAILED
    # Log contains failure message
    assert any("Mission FAILED" in r.message for r in caplog.records)


def test_stop_mission_calls_shutdown_and_marks_finished(tmp_path, monkeypatch, caplog):
    modules_data = [
        {"pkg": "pkg_a", "launch_file": "a.launch", "heartbeats_topic": "hb/a", "is_node_msg": True}
    ]
    write_mission_json(tmp_path, "acceleration", modules_data)
    monkeypatch.chdir(tmp_path)

    comm = CommStub()
    mm_cls = load_mission_manager_class(comm)
    manager = mm_cls()
    mm_cls._instance = manager
    manager.missionFactory = {"acceleration": DummyMission}

    mm = ModuleManagerStub(launch_result=[])
    manager.setModuleManager(mm)
    caplog.set_level(logging.INFO)
    manager.startMission("acceleration")
    active = manager.getActiveMission()
    assert active is not None
    assert active.missionStatus == MissionStatus.RUNNING

    manager.stopMission()

    # The mission object (we held reference) should be FINISHED
    assert active.missionStatus == MissionStatus.FINISHED
    assert mm.shutdown_called is True
    # CommunicationLayer should have been called to unregister (None)
    assert comm.registered[-1] is None
    # Log assertions for stop
    msgs = [r.message for r in caplog.records]
    assert any("Stopping mission" in m for m in msgs)
    assert any("Mission stopped" in m for m in msgs)
