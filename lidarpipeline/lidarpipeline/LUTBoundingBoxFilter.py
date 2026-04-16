"""
LUT Bounding Box Filter - Uses cone detection to create corridors for filtering.
Builds a lookup table based on cone positions and track width.

The ConeClassifier is injected at construction time instead of being created
internally, so callers can use independent classifier instances with different
parameters without hitting SingletonMeta conflicts.
"""
from typing import Dict, List
import open3d as o3d
import numpy as np
from .ConeClassifier import ConeClassifier


class LUTBoundingBoxFilter:
    """
    Look-Up Table Bounding Box filter that uses cone positions to define
    a corridor of interest. Works across frames:
    - Frame 0: Detect cones, compute centerline and width
    - Frame N: Use stored centerline + width for fast filtering
    """

    def __init__(
        self,
        # Shared ground-removal / bounds params
        max_distance: float,
        z_min: float,
        z_max: float,
        ground_level: float,
        point_num: int,
        distance_threshold: float,
        ransac_n: int,
        num_iterations: int,
        horizontal_plane_gradient: float,
        # Cone gating
        max_track_half_width: float,
        max_cone_lateral: float,
        # Cone classifier — injected externally so its parameters are
        # fully independent from the final-classification classifier.
        cone_classifier: ConeClassifier,
        # LUT building
        lut_resolution: float,
        lut_ema_alpha: float,
        lut_max_width_change: float,
        lut_tolerance_multiplier: float,
        # LUT filtering
        lut_filter_margin: float,
        lut_filter_x_margin_before: float,
        lut_filter_x_margin_after: float,
    ):
        self.max_distance = max_distance
        self.z_min = z_min
        self.z_max = z_max
        self.ground_level = ground_level
        self.point_num = point_num
        self.distance_threshold = distance_threshold
        self.ransac_n = ransac_n
        self.num_iterations = num_iterations
        self.horizontal_plane_gradient = horizontal_plane_gradient

        # Use the externally provided classifier (no singleton conflict)
        self.cone_classifier = cone_classifier

        # LUT state
        self.lut_centerline: Dict[float, float] = {}
        self.lut_width: Dict[float, float] = {}
        self.detected_cones: List[np.ndarray] = []

        self.max_track_half_width: float = max_track_half_width
        self.max_cone_lateral: float = max_cone_lateral

        self.lut_resolution: float = lut_resolution
        self.lut_ema_alpha: float = lut_ema_alpha
        self.lut_max_width_change: float = lut_max_width_change
        self.lut_tolerance_multiplier: float = lut_tolerance_multiplier

        self.lut_filter_margin: float = lut_filter_margin
        self.lut_filter_x_margin_before: float = lut_filter_x_margin_before
        self.lut_filter_x_margin_after: float = lut_filter_x_margin_after

        self._lut_filter_diagnostics: dict = {}

    # ------------------------------------------------------------------ #
    # Cone detection and LUT building
    # ------------------------------------------------------------------ #

    def detectCones(
        self, pcd: o3d.geometry.PointCloud, clustering_results: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        Detect cones from clustered points.

        Parameters
        ----------
        pcd : o3d.geometry.PointCloud
        clustering_results : List[np.ndarray]
            List of cluster index arrays from the clustering algorithm.

        Returns
        -------
        List[np.ndarray]
            List of detected cone centres (3-D coordinates).
        """
        cones = []
        points = np.asarray(pcd.points)

        for cluster_indices in clustering_results:
            if len(cluster_indices) > 0:
                cluster_points = points[cluster_indices]
                is_cone, cone_center = self.cone_classifier.isCone(cluster_points)
                if is_cone[0] and cone_center is not None:
                    cones.append(cone_center[0])

        self.detected_cones = cones
        return cones

    def buildLUT(self, cones: List[np.ndarray]) -> None:
        """
        Build the Look-Up Table from detected cone positions.

        For a racing track:
        - Left cones (y > 0) and right cones (y < 0) are paired by x.
        - Centreline: y_center = (y_left + y_right) / 2
        - Half-width:  w = |y_left - y_right| / 2
        EMA smoothing and rate-limiting guard against outliers.
        """
        gated_cones: List[np.ndarray] = []
        for c in cones:
            x_c, y_c, _ = c
            dist = float(np.hypot(x_c, y_c))
            if abs(y_c) > self.max_cone_lateral:
                continue
            if dist > self.max_distance:
                continue
            gated_cones.append(c)

        if len(gated_cones) < 2:
            return

        cones_sorted = sorted(gated_cones, key=lambda c: c[0])
        cones_array = np.array(cones_sorted)

        x_min = cones_array[:, 0].min()
        x_max = cones_array[:, 0].max()
        x_positions = np.arange(x_min, x_max + self.lut_resolution, self.lut_resolution)

        for x in x_positions:
            tolerance = self.lut_resolution * self.lut_tolerance_multiplier
            nearby_cones = cones_array[np.abs(cones_array[:, 0] - x) <= tolerance]

            if len(nearby_cones) >= 2:
                left_cones = nearby_cones[nearby_cones[:, 1] > 0]
                right_cones = nearby_cones[nearby_cones[:, 1] < 0]

                if len(left_cones) > 0 and len(right_cones) > 0:
                    y_left = left_cones[:, 1].mean()
                    y_right = right_cones[:, 1].mean()

                    y_center = (y_left + y_right) / 2.0
                    half_width = np.abs(y_left - y_right) / 2.0

                    if half_width > self.max_track_half_width:
                        continue

                    if x in self.lut_width:
                        if abs(half_width - self.lut_width[x]) > self.lut_max_width_change:
                            continue
                        self.lut_centerline[x] = (
                            self.lut_ema_alpha * y_center
                            + (1 - self.lut_ema_alpha) * self.lut_centerline[x]
                        )
                        self.lut_width[x] = (
                            self.lut_ema_alpha * half_width
                            + (1 - self.lut_ema_alpha) * self.lut_width[x]
                        )
                
                    else:
                        self.lut_centerline[x] = y_center
                        self.lut_width[x] = half_width

        # Sliding window: keep only entries within max_distance of the current
        # cone centre so the LUT stays spatially consistent.
        if self.lut_centerline and len(cones_array) > 0:
            x_center = np.median(cones_array[:, 0])
            x_min_window = x_center - self.max_distance
            x_max_window = x_center + self.max_distance
            for x_old in [
                x for x in list(self.lut_centerline.keys())
                if x < x_min_window or x > x_max_window
            ]:
                self.lut_centerline.pop(x_old, None)
                self.lut_width.pop(x_old, None)

    # ------------------------------------------------------------------ #
    # Filtering
    # ------------------------------------------------------------------ #

    def filterWithLUT(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """
        Filter the point cloud using the built corridor LUT.
        Falls back to basic distance/z bounds until a LUT is available.
        """
        if not self.lut_centerline or not self.lut_width:
            return self._filterBasicBounds(pcd)

        points = np.asarray(pcd.points)
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]

        lut_x_sorted = np.array(sorted(self.lut_centerline.keys()))
        lut_y_arr = np.array([self.lut_centerline[xi] for xi in lut_x_sorted])
        lut_w_arr = np.array([self.lut_width[xi] for xi in lut_x_sorted])

        lut_x_min = float(lut_x_sorted[0])
        lut_x_max = float(lut_x_sorted[-1])

        x_in_range = (
            (x >= lut_x_min - self.lut_filter_x_margin_before)
            & (x <= lut_x_max + self.lut_filter_x_margin_after)
        )

        idx = np.searchsorted(lut_x_sorted, x, side='left')
        idx = np.clip(idx, 0, len(lut_x_sorted) - 1)
        idx_prev = np.maximum(idx - 1, 0)
        use_prev = (idx > 0) & (
            np.abs(lut_x_sorted[idx_prev] - x) < np.abs(lut_x_sorted[idx] - x)
        )
        idx = np.where(use_prev, idx_prev, idx)

        y_center = lut_y_arr[idx]
        half_width = lut_w_arr[idx]

        corridor_mask = np.abs(y - y_center) <= (half_width + self.lut_filter_margin)

        distance = np.sqrt(x**2 + y**2)
        bound_mask = (
            (distance <= self.max_distance)
            & (z >= self.z_min)
            & (z <= self.z_max)
        )

        mask = corridor_mask & bound_mask & x_in_range

        self._lut_filter_diagnostics = {
            'input_count': len(points),
            'corridor_pass': int(np.sum(corridor_mask & x_in_range)),
            'bound_pass': int(np.sum(bound_mask)),
            'final_output': int(np.sum(mask)),
            'margin': self.lut_filter_margin,
            'lut_size': len(self.lut_centerline),
        }

        return pcd.select_by_index(np.where(mask)[0])

    def _filterBasicBounds(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Apply basic distance and z bounds when the LUT is not yet available."""
        points = np.asarray(pcd.points)
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        distance = np.sqrt(x**2 + y**2)
        mask = (
            (distance <= self.max_distance)
            & (z >= self.z_min)
            & (z <= self.z_max)
        )
        return pcd.select_by_index(np.where(mask)[0])

    def clearLUT(self) -> None:
        """Clear the LUT and detected cones."""
        self.lut_centerline.clear()
        self.lut_width.clear()
        self.detected_cones.clear()
