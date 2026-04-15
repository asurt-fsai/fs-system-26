import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/aly-sultan/Desktop/fs-system-25/SLAM/install/cone_a_lisa'
