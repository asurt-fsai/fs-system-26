from typing import Dict, List
import open3d as o3d
import numpy as np
from .helpers import SingletonMeta
class Filter(metaclass=SingletonMeta):

    def __init__(
        self,
        viewableBounds: Dict[str, List[float]],
        carDimensions: Dict[str, List[float]],

        ground_level: float,
        point_num: int,
        distance_threshold: float,
        ransac_n: int,
        num_iterations: int,
        horizontal_plane_gradient: float,

    ):


        self.viewableBounds = viewableBounds
        self.carDimensions = carDimensions
        self.ground_level = ground_level
        self.point_num = point_num      
        self.distance_threshold = distance_threshold
        self.ransac_n = ransac_n
        self.num_iterations = num_iterations
        self.horizontal_plane_gradient = horizontal_plane_gradient

        

    def filterViewableArea(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:

        min_bound = np.array([
            self.viewableBounds["x"][0], 
            self.viewableBounds["y"][0], 
            self.viewableBounds["z"][0]
        ])
        
        max_bound = np.array([
            self.viewableBounds["x"][1], 
            self.viewableBounds["y"][1], 
            self.viewableBounds["z"][1]
        ])

        box = o3d.geometry.AxisAlignedBoundingBox(min_bound, max_bound)
        cropped_pcd = pcd.crop(box)
        return cropped_pcd

    def removeCar(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        points = np.asarray(pcd.points)
        
        x_min, x_max = self.carDimensions["x"]
        y_min, y_max = self.carDimensions["y"]

        mask = ~((points[:, 0] >= x_min) & (points[:, 0] <= x_max) & 
                 (points[:, 1] >= y_min) & (points[:, 1] <= y_max))
        
        return pcd.select_by_index(np.where(mask)[0])

    def removeGround(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        points = np.asarray(pcd.points)


        ground_candidates = np.where(points[:, 2] < self.ground_level)[0]
        
        if len(ground_candidates) > self.point_num:
            ground_pcd = pcd.select_by_index(ground_candidates)
            dist_threshold = self.distance_threshold

            ransac_n = self.ransac_n
            num_iterations = self.num_iterations
            plane_model, inliers = ground_pcd.segment_plane(distance_threshold=dist_threshold, ransac_n=ransac_n, num_iterations=num_iterations)
            if abs(plane_model[2]) > self.horizontal_plane_gradient:
                pcd = pcd.select_by_index(ground_candidates[inliers], invert=True)
        return pcd


    @staticmethod
    def removeIntensity(pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        new_pcd = o3d.geometry.PointCloud()
        new_pcd.points = pcd.points
        return new_pcd
    
    