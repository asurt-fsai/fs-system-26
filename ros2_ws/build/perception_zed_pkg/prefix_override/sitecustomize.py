import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ayasx9/FSAI26/perception_deep_logging/ros2_ws/install/perception_zed_pkg'
