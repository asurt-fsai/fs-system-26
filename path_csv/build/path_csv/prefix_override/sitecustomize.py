import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/fsai/Desktop/IPG_2025Modified/formula-carmaker-fs_2024Modifiednextold/formula-carmaker-fs_2024/FCM_Projects/FS_autonomous/ros/ros2_ws/src/path_csv/install/path_csv'
