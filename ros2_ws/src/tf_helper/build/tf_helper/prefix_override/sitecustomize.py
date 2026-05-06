import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ayasx9/FSAI26/FSAI25_perception/fs-system-26/Perception/ros2_ws/tf_helper/install/tf_helper'
