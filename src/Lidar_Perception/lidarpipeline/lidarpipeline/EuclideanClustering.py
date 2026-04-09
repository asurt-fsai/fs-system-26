from .KdTree import KdTree
import pandas as pd
import copy
import plotly.graph_objects as go
import open3d as o3d
import numpy as np
import sys


class clustering:
    def __init__(self, df_input, display_output_flag=False):
        self.pcd_data = df_input[["X", "Y", "Z"]].reset_index(drop=True)
        self.nrows = len(self.pcd_data)
        
        self.kdtree_main = KdTree()
        self.kdtree_main.build_from_dataframe(self.pcd_data)
        
        self.kdtree_root_node = self.kdtree_main.root
        self.points_np = self.pcd_data.values

   
    def euclidean_clustering(self, distance_threshold, cluster_parameters):
        clusters = {}
        cluster_id = 0
        processed_flag = [False] * self.nrows

        for idx in range(self.nrows):
            if processed_flag[idx]:
                continue

            cluster = self.find_clusters(
                idx,
                distance_threshold,
                processed_flag,
                cluster_parameters
            )


            if len(cluster) >= cluster_parameters["min_size"]:
                clusters[cluster_id] = cluster
                cluster_id += 1

        return clusters

    def get_point(self, index):
        return tuple(self.points_np[index])

    def find_clusters(self, start_index, threshold, processed_flag, cluster_parameters):
        cluster = set()
        stack = [start_index]

        max_size = cluster_parameters.get("max_size", float("inf"))

        while stack:
            idx = stack.pop()
            if processed_flag[idx]:
                continue

            processed_flag[idx] = True
            cluster.add(idx)

            if len(cluster) > max_size:
                break

            point = self.get_point(idx)

            neighbors = self.kdtree_main.search_elements(
                node=self.kdtree_root_node,
                target=point,
                radius=threshold
            )

            for n_idx in neighbors:
                if not processed_flag[n_idx]:
                    stack.append(n_idx)

        return cluster



