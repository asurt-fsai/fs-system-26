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


    def build(self, points, depth=0):
        if not points:
            return None

        axis = depth % 3

        # sort by current axis
        points.sort(key=lambda p: p[0][axis])

        median = len(points) // 2
        point, point_id = points[median]

        node = Node(point, point_id, axis)

        node.left  = self.build(points[:median], depth + 1)
        node.right = self.build(points[median + 1:], depth + 1)

        return node
    

    def build_from_dataframe(self, df):
        # Create the list of ((x,y,z), id) tuples
        points = [((row.X, row.Y, row.Z), idx)
                for idx, row in df.iterrows()]

        # Pass ONLY the points list and the starting depth
        self.root = self.build(points, depth=0)



    def search_elements(self, node, target, radius, results=None):
        if node is None:
            return results

        if results is None:
            results = set()

        dx = node.point[0] - target[0]
        dy = node.point[1] - target[1]
        dz = node.point[2] - target[2]

        if dx*dx + dy*dy + dz*dz <= radius * radius:
            results.add(node.point_id)

        axis = node.axis
        diff = target[axis] - node.point[axis]

        if diff < 0:
            self.search_elements(node.left, target, radius, results)
        else:
            self.search_elements(node.right, target, radius, results)

        if abs(diff) <= radius:
            if diff < 0:
                self.search_elements(node.right, target, radius, results)
            else:
                self.search_elements(node.left, target, radius, results)

        return results
