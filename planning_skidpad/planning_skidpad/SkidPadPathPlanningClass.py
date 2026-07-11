"""Module providing a function printing python version."""

from typing import Tuple
from typing import Dict
import math
import numpy as np
from nav_msgs.msg import Odometry
import matplotlib.pyplot as plt
from tf_transformations import euler_from_quaternion
import random
from collections import deque

class SendPath():
    """
    Class for generating a path for the skidpad.

    Attributes:
        state (Odometry): The current state of the vehicle.
        count (int): The number of orange nodes passed.
        pastPos (np.array): The previous position of the vehicle.
        origin (np.array): The origin of the path.
        threshold (float): The maximum distance between points to merge.
        flag (int): A flag to check if the origin has been set.
        radiusMean (float): The mean radius of the circles.
    """

    def __init__(self) -> None:
        self.state = Odometry()
        self.count = 0
        self.pastPos = np.empty(2)
        self.origin = np.array([15, 0])
        self.threshold = 0.2
        self.radiusMean = 9.125
        self.rightCenter = np.array([15,-9.125])
        self.right_center_history = deque(maxlen=20)
        self.leftCenter = np.array([15,9.125])
        self.left_center_history = deque(maxlen=20)
        self.bigOrangeCones = np.empty((0, 3))
        self.i = 0
        self.saved_orange_nodes = np.empty((0, 3))
        self.saved_orange_nodes_set = False
        self.exit_path = None
        self.exit_path_saved = False

    def conesClassification(
        self, cones: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Classifies cones based on their position relative to the robot's pose.

        Returns:
            Tuple: A tuple containing the classified cones arrays in the following order:
            - rightBlueCones: Array of blue cones on the right side of the robot.
            - leftBlueCones: Array of blue cones on the left side of the robot.
            - rightYellowCones: Array of yellow cones on the right side of the robot.
            - leftYellowCones: Array of yellow cones on the left side of the robot.
            - orangeCones: Array of orange cones.
            - bigOrange: Array of large orange cones.
            - unknownCones: Array of unknown cones.
        """
        # filter_outliers cones based on position and color
        rightBlueCones = np.array(cones[cones[:, 2] == 0][cones[cones[:, 2] == 0][:, 1] < 0])
        leftBlueCones = np.array(cones[cones[:, 2] == 0][cones[cones[:, 2] == 0][:, 1] >= 0])
        rightYellowCones = np.array(cones[cones[:, 2] == 1][cones[cones[:, 2] == 1][:, 1] < 0])
        leftYellowCones = np.array(cones[cones[:, 2] == 1][cones[cones[:, 2] == 1][:, 1] >= 0])
        orangeCones = np.array(cones[cones[:, 2] == 2])
        bigOrange = np.array(cones[cones[:, 2] == 3])
        unknownCones = np.array(cones[cones[:, 2] == 4])

        # Sort cones based on distance from robot's pose
        rightBlueCones = rightBlueCones[
            np.argsort(
                (rightBlueCones[:, 0] - self.state.pose.pose.position.x) ** 2
                + (rightBlueCones[:, 1] - self.state.pose.pose.position.y) ** 2
            )
        ]
        leftBlueCones = leftBlueCones[
            np.argsort(
                (leftBlueCones[:, 0] - self.state.pose.pose.position.x) ** 2
                + (leftBlueCones[:, 1] - self.state.pose.pose.position.y) ** 2
            )
        ]
        rightYellowCones = rightYellowCones[
            np.argsort(
                (rightYellowCones[:, 0] - self.state.pose.pose.position.x) ** 2
                + (rightYellowCones[:, 1] - self.state.pose.pose.position.y) ** 2
            )
        ]
        leftYellowCones = leftYellowCones[
            np.argsort(
                (leftYellowCones[:, 0] - self.state.pose.pose.position.x) ** 2
                + (leftYellowCones[:, 1] - self.state.pose.pose.position.y) ** 2
            )
        ]
        orangeCones = orangeCones[
            np.argsort(
                (orangeCones[:, 0] - self.state.pose.pose.position.x) ** 2
                + (orangeCones[:, 1] - self.state.pose.pose.position.y) ** 2
            )
        ]
        bigOrange = bigOrange[
            np.argsort(
                (bigOrange[:, 0] - self.state.pose.pose.position.x) ** 2
                + (bigOrange[:, 1] - self.state.pose.pose.position.y) ** 2
            )
        ]
        unknownCones = unknownCones[
            np.argsort(
                (unknownCones[:, 0] - self.state.pose.pose.position.x) ** 2
                + (unknownCones[:, 1] - self.state.pose.pose.position.y) ** 2
            )
        ]

        return (
            rightBlueCones,
            leftBlueCones,
            rightYellowCones,
            leftYellowCones,
            orangeCones,
            bigOrange,
            unknownCones,
        )

    def findOrangeNodes(self, orangeConesMap: np.ndarray) -> np.ndarray:
        """
        Finds orange nodes based on specific conditions from the given orange cones map.

        Args:
            orangeConesMap (numpy.ndarray): Array containing nodes information.

        Returns:
            numpy.ndarray: Array of orange nodes that satisfy the conditions.
        """
        # Initialize an empty array to store orange nodes
        orangeNodes = np.zeros((0, 3))

        for cone1 in orangeConesMap:
            lowestDist = float("inf")
            nearestCone = np.zeros((0,))

            # Find the nearest cone to the current cone
            for cone2 in orangeConesMap:
                if not np.array_equal(cone1, cone2) and cone1[1] * cone2[1] < 0:
                    dist = math.sqrt((cone1[0] - cone2[0]) ** 2 + (cone1[1] - cone2[1]) ** 2)
                    if dist < lowestDist:
                        lowestDist = dist
                        nearestCone = cone2
            # Calculate the average position between the current cone and the nearest cone
            if not np.array_equal(nearestCone, np.zeros((0,))):
                avgX = round((cone1[0] + nearestCone[0]) / 2, 2)
                avgY = round((cone1[1] + nearestCone[1]) / 2, 2)
                newNode = np.array([[avgX, avgY, cone1[2]]])

                # Add the new node to the orange nodes array if it does not already exist
                if not np.any(np.all(orangeNodes[:, :2] == newNode[:, :2], axis=1)):
                    orangeNodes = np.concatenate((orangeNodes, newNode), axis=0)
        return orangeNodes

    def dist(self, seta1: float, seta2: float) -> float:
        """
        Calculates the distance between two angles.

        Args:
            seta1 (float): First angle.
            seta2 (float): Second angle.

        Returns:
            float: Distance between the two angles.
        """
        return abs(seta1 - seta2)

    def createStraightPath(self, startPoint: np.array, direction: np.float64, numPoints: int):
        """
        Creates a list of points along a straight path with a given distance between points.

        Args:
            start_point: A tuple (x, y) representing the starting point.
            direction: Direction in degrees (0: right, 90: up, 180: left, 270: down).
            num_points: Total number of points in the path (including the starting point).

        Returns:
            A list of tuples (x, y) representing the points on the path.
        """
        path = np.array([startPoint])
        x, y = startPoint
        # Calculate step vector components
        deltaX = math.cos(direction)
        deltaY = math.sin(direction)

        # Generate subsequent points
        for _ in range(1, numPoints):
            x += deltaX
            y += deltaY
            newPoint = [x,y]
            path = np.row_stack((path, newPoint))

        return path
    

    def createPathToTarget(self, startPoint: np.ndarray, target: np.ndarray, numPoints: int) -> np.ndarray:
        direction = math.atan2(target[1] - startPoint[1], target[0] - startPoint[0])
        return self.createStraightPath(startPoint, direction, numPoints)

    def linePath(self, orangeNodes: np.ndarray, pos: np.ndarray) -> np.ndarray:
        """
        Generates a line path based on orange nodes and a given position.

        Args:
            orangeNodes (np.ndarray): Array of orange nodes.
            pos (list): Current position.

        Returns:
            np.ndarray: Array representing the line path.
        """
        if orangeNodes.shape[0] < 2:
            direction = self.origin - np.array([0,0])
            return self.createStraightPath(pos, math.atan2(direction[1], direction[0]), 5)

        # Initialize variables
        if self.origin[0] != 0:
            x = np.append(orangeNodes[:, 0], self.origin[0])
            y = np.append(orangeNodes[:, 1], self.origin[1])
        else:
            x = orangeNodes[:, 0]
            y = orangeNodes[:, 1]
        noNeedIndex = np.array([], dtype=int)
        path = np.zeros((0, 2))

        # filter_outliers orange nodes based on position
        for i in range(len(orangeNodes)):
            if orangeNodes[i, 1] < pos[1]:
                noNeedIndex = np.append(noNeedIndex, i)
        noNeedIndex = np.flip(noNeedIndex)
        orangeNodes = np.delete(orangeNodes, noNeedIndex, axis=0)

        # Check if there are no orange nodes
        if orangeNodes.shape[0] < 2:
            direction = self.origin - np.array([0,0])
            return self.createStraightPath(pos, math.atan2(direction[1], direction[0]), 5)

        # Generate the path
        try:
            matrix = np.c_[x, np.ones_like(x)]
            slope, const = np.linalg.solve(matrix.T @ matrix, matrix.T @ y)
        except np.linalg.LinAlgError:
            slope = 0
            const = 0

        # Find the end point of the path
        if self.count < 4 and not np.array_equal(self.origin, [0, 0]):
            x = np.linspace(
                float(pos[0]), self.origin[0], int(abs(pos[0] - self.origin[0]) + 1) * 5
            )
        elif self.count < 4:
            x = np.linspace(
                float(pos[0]), float(pos[0]) + 5, int(abs(pos[0] - (float(pos[0]) + 5)) + 1) * 5
            )
        else:
            if orangeNodes.size == 0:
                end = float(pos[0]) + 5
            else:
                end = orangeNodes[:, 0].max()
                if end < float(pos[0]):
                    end = float(pos[0]) + 5
            x = np.linspace(float(pos[0]), end, int(abs(pos[0] - end) + 1) * 10)

        if round(slope, 1) != 0.0:
            path = np.column_stack((x, slope * x + const))
        else:
            path = np.column_stack((x,np.full_like(x, pos[1])))

        return path
    
    def find_circle_center_from_estimate(self, p1, p2, radius, estimated_center):
        """Return the candidate center closer to the estimated one."""
        p1 = p1[:2]
        p2 = p2[:2]
        estimated_center = estimated_center[:2]

        mid = (p1 + p2) / 2
        d = np.linalg.norm(p1 - p2)
        
        if d > 2 * radius:
            return None  # No valid circle
        
        h = np.sqrt(radius**2 - (d/2)**2)
        perp = np.array([-(p2 - p1)[1], (p2 - p1)[0]]) / d  # Normalized perpendicular vector

        center1 = mid + h * perp
        center2 = mid - h * perp

        # Return the one closer to the estimated center
        dist1 = np.linalg.norm(center1 - estimated_center)
        dist2 = np.linalg.norm(center2 - estimated_center)
        return center1 if dist1 < dist2 else center2

    def ransac_circle_with_estimate(self, points: np.ndarray, radius: float, estimated_center: np.array, threshold=0.5, iterations=10):
        best_center = None
        best_inliers = 0
        points_list = list(points)
        if len(points_list) < 2:
            return estimated_center
        for _ in range(iterations):
            p1, p2 = random.sample(points_list, 2)
            center = self.find_circle_center_from_estimate(np.array(p1), np.array(p2), radius, np.array(estimated_center))
            if center is None:
                continue

            inliers = 0
            for pt in points:
                dist = np.linalg.norm(np.array(pt[:2]) - center)
                if abs(dist - radius) <= threshold:
                    inliers += 1
            
            if inliers > best_inliers:
                best_inliers = inliers
                best_center = center
        
        return best_center

    def fitCircle(self, points: np.ndarray) -> Tuple[float, float, float]:
        """
        Fits a circle to the given points using a least squares method.

        Args:
            points (np.ndarray): Array of points.

        Returns:
            Tuple[float, float, float]:
            x-coordinate of the center, y-coordinate of the center, and radius of the circle.
        """
        if len(points) < 3:
            return self.rightCenter[0], self.rightCenter[1], self.radiusMean
        # Fit a circle to the given points
        matrix = np.c_[-2 * points[:, 0], -2 * points[:, 1], np.ones_like(points[:, 0])]
        # Solve the linear system of equations
        xRightCenter, yRightCenter, const = np.linalg.solve(
            matrix.T @ matrix, matrix.T @ (-points[:, 0] ** 2 - points[:, 1] ** 2)
        )
        # Calculate the radius of the circle
        radius = np.sqrt(xRightCenter**2 + yRightCenter**2 - const)

        return xRightCenter, yRightCenter, radius

    def meanCircles(self,outerCones: np.ndarray, innerCones: np.ndarray, estimatedCenter: np.array)->Tuple[float,float,float]:
        """
        Calculates the mean circle from outer and inner cones.

        Args:
            outer_cones (np.ndarray): Array of outer cones.
            inner_cones (np.ndarray): Array of inner cones.

        Returns:
            Tuple[float, float, np.ndarray]: x-coordinate of the center mean, y-coordinate of the center mean,
            and array of mean radii.
        """
        # Fit circles to the given cones
        bestCenter1 = self.ransac_circle_with_estimate(points=outerCones,
                                                            radius=self.radiusMean - 1.5,
                                                            estimated_center=estimatedCenter,
                                                            iterations=len(outerCones))
        bestCenter2 = self.ransac_circle_with_estimate(points=innerCones,
                                                            radius=self.radiusMean + 1.5,
                                                            estimated_center=estimatedCenter,
                                                            iterations=len(innerCones))

        # Calculate the mean of the circle
        if bestCenter1 is not None and bestCenter2 is not None:
            bestCenter = (bestCenter1 + bestCenter2)/2
        elif bestCenter2 is not None:
            bestCenter = bestCenter2
        elif bestCenter1 is not None:
            bestCenter = bestCenter1
        else:
            bestCenter = estimatedCenter
        return bestCenter

    def _circularPath(self, center: np.ndarray, pos: np.ndarray, clockwise: bool) -> np.ndarray:

        start = math.atan2(pos[1] - center[1], pos[0] - center[0])
        end = start - 2 * math.pi if clockwise else start + 2 * math.pi

        n_points = int(self.dist(start, end) + 1) * 5
        theta = np.linspace(start, end, n_points)

        x = self.radiusMean * np.cos(theta) + center[0]
        y = self.radiusMean * np.sin(theta) + center[1]

        return np.column_stack((x, y))


    def rightCirclePath(self, pos: np.ndarray = np.array([0, 0])) -> np.ndarray:
        if np.array_equal(pos, np.array([0, 0])):
            pos = np.array([self.rightCenter[0], self.rightCenter[1] + self.radiusMean])
        return self._circularPath(self.rightCenter, pos, clockwise=True)


    def leftCirclePath(self, pos: np.ndarray = np.array([0, 0])) -> np.ndarray:
        if np.array_equal(pos, np.array([0, 0])):
            pos = np.array([self.leftCenter[0], self.leftCenter[1] - self.radiusMean])
        return self._circularPath(self.leftCenter, pos, clockwise=False)

    def counter(self, pos: np.ndarray) -> None:
        """
        Counts the number of orange nodes passed in and updates internal state.

        Args:
            pos (np.array): Current position [x, y].
            bigOrange (np.array): Array of big orange nodes.

        Returns:
            None
        """
        # Check if the robot has passed an orange node and update the counter and origin
        if np.array_equal(self.origin, np.array([0, 0])):
            return None

        # Define crossing zone tolerance
        y_tolerance = 2.0  # meters

        # Check if we're within the x-coordinate counting zone
        y_within_zone = abs(pos[1] - self.origin[1]) < y_tolerance

        # Detect crossing from either direction
        crossing_right = (pos[0] > self.origin[0]) and (self.pastPos[0] <= self.origin[0])

        # Make sure we're not too far from the origin in x-direction
        if y_within_zone and crossing_right:
            self.count += 1

        return None

    def getOrigin(self) -> None:
        """
        Gets the origin based on the given cones.

        Args:
            bigOrange (np.ndarray): Array of big orange cones.
            leftBlueCones (np.ndarray): Array of left blue cones.
            rightYellowCones (np.ndarray): Array of right yellow cones.

        Returns:
            None
        """
        if len(self.left_center_history) > 0 and len(self.right_center_history) > 0:
            self.origin = (self.leftCenter + self.rightCenter) / 2
        elif len(self.bigOrangeCones) >= 4:
            # The center of 4 points forming a rectangle is simply their average (centroid).
            # This is mathematically equivalent to the diagonal midpoints, but bug-free.
            self.origin = np.mean(self.bigOrangeCones[:4, :2], axis=0)
        elif len(self.right_center_history) > 0:
            self.origin = np.array([self.rightCenter[0] , self.rightCenter[1] + self.radiusMean])
        elif len(self.left_center_history) > 0:
            self.origin = np.array([self.leftCenter[0] , self.leftCenter[1] - self.radiusMean])
        else:
            self.origin = (self.leftCenter + self.rightCenter) / 2

    def get_smoothed_center(self, center_history):
        if len(center_history) == 0:
            return None

        points = np.array(center_history)
        mean = np.mean(points, axis=0)
        return mean

    def classifyPoints(self, colorPoints: np.ndarray, unknownPoints: np.ndarray) -> np.ndarray:
        """
        Classifies unknown points as inside
        or outside of a given circle based on the center and radius.

        Args:
            colorPoints:
            np.ndarray representing points with known color, including the color value.
            unknown_points: np.ndarray representing points with unknown color.

        Returns:
            np.ndarray: Array of classified points.
        """
        if len(colorPoints) == 0:
            return colorPoints
        classifiedPoints = colorPoints
        xRightCenter, yRightCenter, radius = self.fitCircle(colorPoints)
        for point in unknownPoints:
            x, y = point[0], point[1]
            distance = math.sqrt((x - xRightCenter) ** 2 + (y - yRightCenter) ** 2)
            if abs(distance - radius) <= self.threshold:
                classifiedPoints = np.append(classifiedPoints, [[x, y, colorPoints[0, 2]]], axis=0)
        return classifiedPoints

    def getCirclesCenters(
        self,
        leftBlueCones: np.ndarray,
        leftYellowCones: np.ndarray,
        rightYellowCones: np.ndarray,
        rightBlueCones: np.ndarray
    ):
        # Compute potential new centers
        new_right_center = np.array([0, 0])
        new_left_center = np.array([0, 0])

        # Calculate right circle center
        if len(rightYellowCones) >= 2 and len(rightBlueCones) >= 2:
            new_right_center = self.meanCircles(rightYellowCones, rightBlueCones, self.rightCenter)
        elif len(rightYellowCones) >= 2:
            new_right_center = self.ransac_circle_with_estimate(points=rightYellowCones,
                                                            radius=self.radiusMean - 1.5,
                                                            estimated_center=self.rightCenter,
                                                            iterations=len(rightYellowCones))
        elif len(rightBlueCones) >= 2:
            new_right_center = self.ransac_circle_with_estimate(points=rightBlueCones,
                                                            radius=self.radiusMean + 1.5,
                                                            estimated_center=self.rightCenter,
                                                            iterations=len(rightBlueCones))
        # handle with big orange cones
        elif len(self.bigOrangeCones) > 2:
            rightOrangeCones = np.array(self.bigOrangeCones[self.bigOrangeCones[:, 1] < 0])
            if len(rightOrangeCones) == 2:
                new_right_center = self.ransac_circle_with_estimate(points=rightOrangeCones,
                                                            radius=self.radiusMean - 1.5,
                                                            estimated_center=self.rightCenter,
                                                            iterations=len(rightOrangeCones))

        # Calculate left circle center
        if len(leftBlueCones) >= 2 and len(leftYellowCones) >= 2:
            new_left_center= self.meanCircles(leftBlueCones, leftYellowCones, self.leftCenter)
        elif len(leftBlueCones) >= 2:
            new_left_center = self.ransac_circle_with_estimate(points=leftBlueCones,
                                                            radius=self.radiusMean - 1.5,
                                                            estimated_center=self.leftCenter,
                                                            iterations=len(leftBlueCones))
        elif len(leftYellowCones) >= 2:
            new_left_center = self.ransac_circle_with_estimate(points=leftYellowCones,
                                                            radius=self.radiusMean + 1.5,
                                                            estimated_center=self.leftCenter,
                                                            iterations=len(leftYellowCones))
        # handle with big orange cones
        elif len(self.bigOrangeCones) > 2:
            leftOrangeCones = np.array(self.bigOrangeCones[self.bigOrangeCones[:, 1] > 0])
            if len(leftOrangeCones) == 2:
                new_left_center = self.ransac_circle_with_estimate(points=leftOrangeCones,
                                                            radius=self.radiusMean - 1.5,
                                                            estimated_center=self.leftCenter,
                                                            iterations=len(leftOrangeCones)*3)
        if new_right_center is not None:
            if np.linalg.norm(new_right_center - self.rightCenter) < 5.0:
                self.right_center_history.append(new_right_center)
                smoothedRightCenter = self.get_smoothed_center(self.right_center_history)
                if smoothedRightCenter is not None:
                    self.rightCenter = smoothedRightCenter

        if new_left_center is not None:
            if np.linalg.norm(new_left_center - self.leftCenter) < 5.0:
                self.left_center_history.append(new_left_center)
                smoothedLeftCenter = self.get_smoothed_center(self.left_center_history)
                if smoothedLeftCenter is not None:
                    self.leftCenter = smoothedLeftCenter

    def connect_paths(self, path1, path2, car_pos, max_gap=1.0):
        """
        Connects two paths by adding intermediate points if the gap is too large.
        
        Args:
            path1: First path (numpy array of points)
            path2: Second path (numpy array of points)
            max_gap: Maximum allowed distance between consecutive points
            
        Returns:
            Connected path as numpy array
        """
        if len(path2) == 0:
            return np.concatenate((path1, path2), axis=0)
        # Get last point of first path and first point of second path
        elif len(path1) == 0:
            last_point = car_pos
        else:
            last_point = path1[-1]
        first_point = path2[0]
        
        # Calculate distance between paths
        distance = np.linalg.norm(last_point - first_point)
        
        if distance > max_gap:
            # Calculate number of points needed
            num_points = int(np.ceil(distance / max_gap)) - 1
            
            # Create intermediate points
            interpolated_points = np.zeros((num_points, 2))  # Assuming 2D points
            for i in range(num_points):
                t = (i + 1) / (num_points + 1)
                interpolated_points[i] = last_point * (1 - t) + first_point * t
            # Concatenate all paths
            return np.concatenate((path1, interpolated_points, path2), axis=0)
        else:
            return np.concatenate((path1, path2), axis=0)

    def path(
        self,
        leftBlueCones: np.ndarray,
        leftYellowCones: np.ndarray,
        rightYellowCones: np.ndarray,
        rightBlueCones: np.ndarray,
        orange: np.ndarray
    ) -> np.ndarray:
        """
        Generates a path based on the given cones and current state.

        Args:
            rightBlueCones (np.array): Right blue cones.
            leftBlueCones (np.array): Left blue cones.
            rightYellowCones (np.array): Right yellow cones.
            leftYellowCones (np.array): Left yellow cones.
            orangeCones (np.array): Orange cones.
            bigOrange (np.array): Big orange cones.
            unknownCones (np.array): Unknown cones.

        Returns:
            np.array: Generated path as a NumPy array.
        """
        # Initialize variables
        path = np.empty((0, 2))  # Initialize an empty NumPy array
        # Get the current position
        pos = np.array([self.state.pose.pose.position.x, self.state.pose.pose.position.y])
        # Sort orange cones based on distance from robot's pose
        orange = orange[np.lexsort(((orange[:, 1] - pos[1]) ** 2 + (orange[:, 0] - pos[0]) ** 2,))]
        # Find orange nodes
        orangeNodes = self.findOrangeNodes(orange)
        # Save Cones that produced valid straight path
        if self.count < 1 and len(orangeNodes) >= 2 and self.saved_orange_nodes_set == False:
            self.saved_orange_nodes = orangeNodes.copy()
            self.saved_orange_nodes_set = True
        # update the counter based on the current position
        self.getOrigin()
        self.counter(pos)
        self.getCirclesCenters(leftBlueCones,leftYellowCones,rightYellowCones,rightBlueCones)
        # Generate the path based on the current count
        if self.count < 1:
            path = self.linePath(orangeNodes, pos)
            path = self.connect_paths(path, self.rightCirclePath(), pos)
        elif self.count < 2:
            tangent = np.array([
                self.rightCenter[0],
                self.rightCenter[1] + self.radiusMean
            ])

            if np.linalg.norm(pos - tangent) < 2.4:
                path = self.rightCirclePath(pos)
            else:
                path = self.connect_paths(
                    self.linePath(orangeNodes, pos),
                    self.rightCirclePath(),
                    pos
                )

        elif self.count < 3:
            path = self.rightCirclePath(pos)
            path = np.concatenate((path, self.leftCirclePath()), axis=0)
        elif self.count < 4:
            path = self.leftCirclePath(pos)
            path = np.concatenate((path, self.leftCirclePath()), axis=0)
        elif self.count < 5:
            path = self.leftCirclePath(pos)
            if self.exit_path_saved:
                path = np.concatenate((path, self.createPathToTarget(pos, np.array([self.origin[0] + 20, self.origin[1]]), 20)), axis=0)
            elif pos[0] > self.origin[0] - 8:
                self.exit_path_saved = True
                path = np.concatenate((path, self.createPathToTarget(pos, np.array([self.origin[0] + 20, self.origin[1]]), 20)), axis=0)

            # if self.exit_path_saved:
            #     path = np.concatenate((path, self.exit_path[self.exit_path[:, 0] >= pos[0] - 1]), axis=0)
            # elif pos[0] > self.origin[0] - 8:
            #     self.exit_path = self.createStraightPath(pos, self.carDirection, 30)
            #     self.exit_path_saved = True
            #     path = np.concatenate((path, self.exit_path), axis=0)
            # if not self.exit_path_saved and pos[0] > self.origin[0] - 8:
            # # Save exit path early, before reaching origin
            #     self.exit_path = self.createStraightPath(pos, self.carDirection, 30)
            #     self.exit_path_saved = True
    
            # if self.exit_path_saved:
            # # Extend saved path forward from car position
            #     path = self.exit_path[self.exit_path[:, 0] >= pos[0] - 1]
            #     if len(path) < 5:
            #         path = self.createStraightPath(pos, self.carDirection, 30)
            #     return path
            # else:
            #     path = self.leftCirclePath(pos)
            #     path = np.concatenate((path, self.leftCirclePath()), axis=0)
            # path = self.leftCirclePath(pos)
            # if len(orangeNodes) > 0 and pos[0] < self.origin[0]:
            #     path = np.concatenate((path, self.linePath(orangeNodes, path[-1])), axis=0)
            # path = self.leftCirclePath(pos)
            # if pos[0] > self.origin[0] - 3:
            #     path = np.concatenate((path, self.createStraightPath(path[-1], self.carDirection, 15)), axis=0)
        elif self.count >= 5:
            path = self.createPathToTarget(pos, np.array([self.origin[0] + 20, self.origin[1]]), 20)
            # path = self.exit_path[self.exit_path[:, 0] >= pos[0] - 1]
            # if len(path) < 5:
            #     path = self.createStraightPath(pos, self.carDirection, 30)
            # if self.exit_path_saved:
            #     path = self.exit_path[self.exit_path[:, 0] >= pos[0] - 1]
            #     if len(path) < 5:
            #         path = self.createStraightPath(pos, self.carDirection, 30)
            # else:
            #     path = self.createStraightPath(pos, self.carDirection, 20)
            # if np.linalg.norm([pos[0] - self.origin[0], pos[1] - self.origin[1]]) > 20:
            #     return path
            # orangeNodes_small = self.findOrangeNodes(orangeCones)
            # ahead_nodes = orangeNodes_small[orangeNodes_small[:, 0] > pos[0]]
            # if ahead_nodes.shape[0] > 0:
            #     path = self.linePath(ahead_nodes, pos)
            # if self.saved_orange_nodes_set:
            #     n1 = self.saved_orange_nodes[-2]
            #     n2 = self.saved_orange_nodes[-1]
            #     direction = math.atan2(n2[1] - n1[1], n2[0] - n1[0])
            #     path = self.createStraightPath(pos, direction, 8)
            # else:
            # path = self.linePath(orangeNodes, pos)
            # path = self.createStraightPath(pos, self.carDirection, 20)

        return path

    def orangeFilter(self, orangeCones: np.ndarray) -> np.ndarray:
        """
        Filters out the orange cones that are outside the track.

        Args:
            orangeCones (np.ndarray): Array of orange cones.

        Returns:
            np.ndarray: Filtered array of orange cones.
        """
        for cone in orangeCones:
            if cone[1] < -1.7:
                orangeCones = np.delete(
                    orangeCones, np.where((orangeCones == cone).all(axis=1)), axis=0
                )
            elif cone[1] > 1.7:
                orangeCones = np.delete(
                    orangeCones, np.where((orangeCones == cone).all(axis=1)), axis=0
                )
        # rightOrangeCones = np.array(orangeCones[orangeCones[:, 0] > 0])
        # leftOrangeCones = np.array(orangeCones[orangeCones[:, 0] <= 0])
        return orangeCones

    def getPath(self, state: Odometry, cones: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates a path based on the given cones and current state.

        Args:
            state (Odometry): Current state.
            cones (np.ndarray): Array of cones.
             
        Returns:
            Tuple[np.ndarray, np.ndarray]:
              Generated path as a NumPy array and the merged cones array.
        """
        # Store the previous position if the current state is not None
        if self.state is not None:
            self.pastPos = np.array(
                [self.state.pose.pose.position.x, self.state.pose.pose.position.y]
            )
        self.state = state
        orientationQ = state.pose.pose.orientation
        orientationList = [orientationQ.x, orientationQ.y, orientationQ.z, orientationQ.w]
        (_, _, yaw) = euler_from_quaternion(orientationList)
        self.carDirection = yaw

        # # Merge cones that are close to each other
        # if len(cones) > 300:
        #     returnCones = self.mergePoints(cones, self.threshold)
        #     cones = returnCones
        # else:
        #     returnCones = cones
        #     cones = self.mergePoints(cones, self.threshold)
        # initialize variables
        rightBlueCones = np.empty((0, 3))
        leftBlueCones = np.empty((0, 3))
        rightYellowCones = np.empty((0, 3))
        leftYellowCones = np.empty((0, 3))
        orangeCones = np.empty((0, 3))
        unknownCones = np.empty((0, 3))
        # Classify cones based on their position and color
        (
            rightBlueCones,
            leftBlueCones,
            rightYellowCones,
            leftYellowCones,
            orangeCones,
            self.bigOrangeCones,
            unknownCones,
        ) = self.conesClassification(cones)
        # Filter out the orange cones
        orangeCones = self.orangeFilter(np.concatenate((orangeCones, self.bigOrangeCones), axis=0))
        # Classify unknown cones based on the known cones
        # if len(rightBlueCones) >= 3:
        #     rightBlueCones = self.classifyPoints(rightBlueCones, unknownCones)
        # if len(leftBlueCones) >= 3:
        #     leftBlueCones = self.classifyPoints(leftBlueCones, unknownCones)
        # if len(rightYellowCones) >= 3:
        #     rightYellowCones = self.classifyPoints(rightYellowCones, unknownCones)
        # if len(leftYellowCones) >= 3:
        #     leftYellowCones = self.classifyPoints(leftYellowCones, unknownCones)
        # Generate the path
        path = self.path(leftBlueCones,leftYellowCones, rightYellowCones, rightBlueCones, orangeCones)
    

        return path
