import numpy as np
from .KdTree import KdTree
class clustering:
    def __init__(self, df_input):
        self.pcd_data = df_input[["X", "Y", "Z"]].reset_index(drop=True)
        self.points_np = self.pcd_data.values
        self.nrows = len(self.pcd_data)
        
        self.kdtree_main = KdTree()
        self.kdtree_main.build_from_dataframe(self.pcd_data)
        self.kdtree_root_node = self.kdtree_main.root

    def mean_shift_clustering(self, bandwidth, min_points=5,
                          convergence_threshold=0.01,
                          max_iterations=10):
        """
        Optimized Mean Shift Clustering for LiDAR point clouds.

        :param bandwidth: Radius of search (e.g. 0.3 for cones)
        :param min_points: Minimum points to form a valid cluster
        :param convergence_threshold: Stop shifting if movement < threshold
        :param max_iterations: Max shift iterations per seed
        """

        n = self.nrows
        visited = np.zeros(n, dtype=bool)
        clusters = {}
        cluster_id = 0

        for i in range(n):

            if visited[i]:
                continue

            current_mean = self.points_np[i]

            # ---- Mean Shift Loop ----
            for _ in range(max_iterations):

                neighbors_idx = self.kdtree_main.search_elements(
                    node=self.kdtree_root_node,
                    target=tuple(current_mean),
                    radius=bandwidth
                )

                # Early noise rejection
                if len(neighbors_idx) < min_points:
                    break

                neighbor_points = self.points_np[list(neighbors_idx)]
                new_mean = np.mean(neighbor_points, axis=0)

                shift = np.linalg.norm(new_mean - current_mean)
                current_mean = new_mean

                if shift < convergence_threshold:
                    break

            # ---- Final grouping around converged mean ----
            final_neighbors = self.kdtree_main.search_elements(
                node=self.kdtree_root_node,
                target=tuple(current_mean),
                radius=bandwidth / 2
            )

            if len(final_neighbors) >= min_points:

                cluster_members = []

                for idx in final_neighbors:
                    if not visited[idx]:
                        visited[idx] = True
                        cluster_members.append(idx)

                if len(cluster_members) >= min_points:
                    clusters[cluster_id] = set(cluster_members)
                    cluster_id += 1

            else:
                visited[i] = True  # mark noise as visited

        return clusters