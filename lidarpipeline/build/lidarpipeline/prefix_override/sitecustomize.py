import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/spacecraft/fs-system-25/lidarpipeline/install/lidarpipeline'
