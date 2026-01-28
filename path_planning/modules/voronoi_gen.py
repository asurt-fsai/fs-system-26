# path_planning/voronoi_gen.py
import numpy as np
from scipy.spatial import Voronoi


def generate_voronoi(cone_data):
    """
    Extracts coordinates and generates the raw Voronoi object.
    Args:
        cone_data: List of (x, y, color)
    Returns:
        points (np.array): Only the (x,y) parts
        colors (list): Only the color parts
        vor (Voronoi obj): The raw diagram
    """
    if len(cone_data) < 3:
        return None, None, None

    # Separate logic to split the tuple [(x,y,c)] into two lists
    points = np.array([[item[0], item[1]] for item in cone_data])
    colors = [item[2] for item in cone_data]

    vor = Voronoi(points)

    return points, colors, vor