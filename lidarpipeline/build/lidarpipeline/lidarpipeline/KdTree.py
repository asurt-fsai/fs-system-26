class Node:
    def __init__(self, point, point_id, axis):
        self.point = point        # (x, y, z)
        self.point_id = point_id # index of the point in the original dataset
        self.axis = axis       # axis: 0 for x, 1 for y, 2 for z
        self.left = None
        self.right = None



class KdTree:
    """
    Implementation of KDtree
    """
    def __init__(self):
        self.root = None


    def build(self, px, py, pz, depth): # px, py, pz are lists of (point, point_id) sorted by x, y, z respectively
        if not px: # If there are no points left to build the tree, return None
            return None

        axis = depth % 3 # 0 for x, 1 for y, 2 for z

        if axis == 0: # Sort by x-axis
            points_axis = px
        elif axis == 1: # Sort by y-axis
            points_axis = py
        else: # Sort by z-axis
            points_axis = pz

        median_idx = len(points_axis) // 2 # Find the median index
        median_point, median_id = points_axis[median_idx] # Get the median point and its original index

        node = Node(median_point, median_id, axis)

        # Partition points into left/right (based on median)
        left_set = set(p[1] for p in points_axis[:median_idx])

        px_left  = [p for p in px if p[1] in left_set]
        px_right = [p for p in px if p[1] not in left_set and p[1] != median_id]

        py_left  = [p for p in py if p[1] in left_set]
        py_right = [p for p in py if p[1] not in left_set and p[1] != median_id]

        pz_left  = [p for p in pz if p[1] in left_set]
        pz_right = [p for p in pz if p[1] not in left_set and p[1] != median_id]

        node.left  = self.build(px_left, py_left, pz_left, depth + 1)
        node.right = self.build(px_right, py_right, pz_right, depth + 1)

        return node


    def build_from_dataframe(self, df): 
        points = [((row.X, row.Y, row.Z), idx) # Create a list of tuples: ((x, y, z), point_id)
                for idx, row in df.iterrows()] 

        points_x = sorted(points, key=lambda p: p[0][0])
        points_y = sorted(points, key=lambda p: p[0][1])
        points_z = sorted(points, key=lambda p: p[0][2])

        self.root = self.build(points_x, points_y, points_z, depth=0)



    def search_elements(self, node, target, radius, results=None): # node is the current node in the KD-tree, target is the point we are searching around, radius is the search radius, results is a set to store found point_ids
        if node is None:
            return results

        if results is None:
            results = set() # Initialize results set on the first call

        dx = node.point[0] - target[0] # Calculate the distance from the current node's point to the target point
        dy = node.point[1] - target[1] 
        dz = node.point[2] - target[2]

        # If the distance is within the radius, add the point_id to the results
        if dx*dx + dy*dy + dz*dz <= radius * radius:
            results.add(node.point_id)

        # Recursively search the side of the tree that the target point is on, and also check the other side if necessary
        axis = node.axis
        diff = target[axis] - node.point[axis]

        if diff < 0:
            self.search_elements(node.left, target, radius, results)
        else:
            self.search_elements(node.right, target, radius, results)

        # Check if we need to search the other side of the tree (if the hypersphere intersects the splitting plane)
        if abs(diff) <= radius:
            if diff < 0:
                self.search_elements(node.right, target, radius, results)
            else:
                self.search_elements(node.left, target, radius, results)

        return results # Return the set of point_ids that are within the radius of the target point
