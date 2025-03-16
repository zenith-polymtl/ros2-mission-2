import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/colin/ardupilot_sim/ardu_ws/src/mission/install/mission'
