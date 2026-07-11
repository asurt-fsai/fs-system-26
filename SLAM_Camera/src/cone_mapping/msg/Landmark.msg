# Position in camera frame
geometry_msgs/Point position
#   float64 x  # Forward
#   float64 y  # Lateral
#   float64 z  # Height

# Cone type/color
int32 type
#   # 0 = Blue
#   # 1 = Yellow
#   # 2 = Orange
#   # 3 = Unknown

# Tracking ID (unstable, ignored by mapper)
int32 identifier

# Detection confidence
float32 probability  # Range: [0.0, 1.0]
