class Node:
    def __init__(self, point, point_id, axis):
        self.point = point
        self.point_id = point_id
        self.axis = axis
        self.left = None
        self.right = None



class KdTree:
    def __init__(self):
        self.root = None


    def build(self, px, py, pz, depth):
        if not px:
            return None

        axis = depth % 3

        if axis == 0:
            points_axis = px
        elif axis == 1:
            points_axis = py
        else:
            points_axis = pz

        median_idx = len(points_axis) // 2
        median_point, median_id = points_axis[median_idx]

        node = Node(median_point, median_id, axis)

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
        points = [((row.X, row.Y, row.Z), idx)
                for idx, row in df.iterrows()]

        points_x = sorted(points, key=lambda p: p[0][0])
        points_y = sorted(points, key=lambda p: p[0][1])
        points_z = sorted(points, key=lambda p: p[0][2])

        self.root = self.build(points_x, points_y, points_z, depth=0)



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
