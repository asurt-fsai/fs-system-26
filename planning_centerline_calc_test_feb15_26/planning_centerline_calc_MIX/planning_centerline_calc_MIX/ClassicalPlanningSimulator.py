from __future__ import annotations
import json
import math
import random
from matplotlib import animation
import numpy as np
from scipy.spatial import distance
import matplotlib.pyplot as plt
from icecream import ic
from src.full_pipeline.full_pipeline import PathPlanner
from src.utils.cone_types import ConeTypes
from IPython.display import HTML



class ClassicalPlanningSimulator:
    """
    Class responsible for running our matplotlib simulator for a given track
    
    Attributes:
    simulationParameters : SimulationParameters
    isVideoOutput: Boolean
    
    Methods:
    
    """
    simulationParameters: SimulationParameters
    pathPlanner: PathPlanner
    simulation: list[HTML]
    
    def __init__(self, simulationParameters) -> None:
        self.simulationParameters = simulationParameters
        self.simulation = []
        pass
    
    def setSimulationParameters(self, simulationParameters: SimulationParameters) -> None:
        self.simulationParameters = simulationParameters

    def plotSampleWithCar(self):
        startX = self.simulationParameters.startPos[0]
        startY = self.simulationParameters.startPos[1]
        startDir = self.simulationParameters.startDir
        radius = self.simulationParameters.viewRadius
        Maskx, Masky = create_semicircle([startX, startY], startDir, radius)
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.simulationParameters.track.x_blue, self.simulationParameters.track.y_blue, marker='o', linestyle='-', color='blue', label='Blue Cones', markersize=4)
        plt.plot(self.simulationParameters.track.x_yellow, self.simulationParameters.track.y_yellow, marker='o', linestyle='-', color='yellow', label='Yellow Cones', markersize=4)
        plt.plot(self.simulationParameters.track.x_path, self.simulationParameters.track.y_path, marker='', linestyle='-', color='black', label='Path')
        
        plt.plot(startX, startY, marker = 'o', color = "red")
        plt.plot(Maskx, Masky, color = "red")
        plt.show()
        pass
    
    def runSimulator(self, pathPlanner: PathPlanner, frames: int, createVideo: bool = True) -> None:
        self.pathPlanner = pathPlanner
        fig = plt.figure(figsize=(12, 5))
        ax1 = plt.subplot(1,2,1)
        ax2 = plt.subplot(1,2,2)

        ax1.set_title("Map")
        ax2.set_title("Path")

        ax1.plot(self.simulationParameters.track.x_blue, self.simulationParameters.track.y_blue, marker='o', linestyle='-', color='blue', label='Blue Cones', markersize=4)
        ax1.plot(self.simulationParameters.track.x_yellow, self.simulationParameters.track.y_yellow, marker='o', linestyle='-', color='yellow', label='Yellow Cones', markersize=4)

        pos1, = ax1.plot([], [], marker = 'o', color = "red") # Position
        SC, = ax1.plot([], [], color = "red") #SemiCircle
        path1, = ax1.plot([], [], c='black', label="path") #Path
        
        #Initial Path
        conesInput = [np.zeros((0, 2)) for _ in ConeTypes]
        conesInput[ConeTypes.BLUE] = np.vstack((conesInput[ConeTypes.BLUE], self.simulationParameters.conesBlueInView))
        conesInput[ConeTypes.YELLOW] = np.vstack((conesInput[ConeTypes.YELLOW], self.simulationParameters.conesYellowInView))
        """ Could be optimized by not calculating initial path twice """
        """ Could the problem simply be that the initial path is calculated outside the semicircle? """
        """ Could the problem simply be a simulation visualization issue, not an algorithmic issue? """
        ### I'm tired boss ###
        path = pathPlanner.calculatePathInGlobalFrame(vehiclePosition=self.simulationParameters.startPos, 
                                                      vehicleDirection= self.simulationParameters.startDir, # type: ignore
                                                      cones=conesInput)
        
        def updatePaths(path, radius):
            paths = []
            Maskxs = []
            Maskys = []
            poss = []
            blues = []
            yellows = []
            cornerFlags = []
            normalFlags = []
            
            # --- Logic for Lap Completion ---
            min_lap_distance = 300.0 # Minimum distance traveled before we consider finishing
            total_distance = 0.0     # Tracker for total distance traveled
            finish_radius = 4.0      # Increased slightly to ensure detection
            frames_after_finish = 20 # Continue for 20 frames to show crossing
            finish_counter = 0
            # -------------------------------

            for n in range (frames):

                # Safety check: if path is too short, we can't index into it
                if len(path) == 0:
                    break
                
                pos = path[int(len(path)/4)]

                next_idx = int(len(path)/4) + 1
                if next_idx < len (path):
                    dir = math.atan2(path[next_idx][1] - pos[1], path[next_idx][0] - pos[0])
                else:
                    dir = self.simulationParameters.startDir    # Fallback
                
                # --- STOPPING LOGIC START ---
                dist_to_start = distance.euclidean(pos, self.simulationParameters.startPos)

                # Update total distance traveled
                if n > 0:
                     step_dist = distance.euclidean(pos, poss[-1])
                     total_distance += step_dist

                # Check if we have returned to the start area after traveling enough distance
                if total_distance > min_lap_distance and dist_to_start < finish_radius:
                    if finish_counter == 0:
                        print(f"Lap Finished at frame {n}. Final Distance to start: {dist_to_start:.2f}. Total Distance: {total_distance:.2f}. Running extra frames...")
                    
                    finish_counter += 1
                    """
                    if finish_counter >= frames_after_finish:
                        #capture final frame data before breaking so the graph updates one last time
                        Maskx, Masky = create_semicircle(pos, dir, radius)

                        # Add current state to lists
                        cornerFlags.append(pathPlanner.cornerCaseFlag)
                        normalFlags.append(pathPlanner.normalCaseFlag)
                        paths.append(path)
                        Maskxs.append(Maskx)
                        Maskys.append(Masky)
                        poss.append(pos)
                        
                        #Need to query cones one last time for the final frame visualization
                        coneBlueINSemiCircle = self.simulationParameters.track.cones_blue[is_inside_semicircle(pos, dir, radius, self.simulationParameters.track.cones_blue)]
                        conesYellowInSemiCircle = self.simulationParameters.track.cones_yellow[is_inside_semicircle(pos, dir, radius, self.simulationParameters.track.cones_yellow)]
                        blues.append(coneBlueINSemiCircle)
                        yellows.append(conesYellowInSemiCircle)
                        break
                    """
                # --- STOPPING LOGIC END ---
                
                coneBlueINSemiCircle = self.simulationParameters.track.cones_blue[is_inside_semicircle(pos, dir, radius, self.simulationParameters.track.cones_blue)]
                conesYellowInSemiCircle = self.simulationParameters.track.cones_yellow[is_inside_semicircle(pos, dir, radius, self.simulationParameters.track.cones_yellow)]
                
                conesInput = [np.zeros((0, 2)) for _ in ConeTypes]
                conesInput[ConeTypes.BLUE] = np.vstack((conesInput[ConeTypes.BLUE], coneBlueINSemiCircle))
                conesInput[ConeTypes.YELLOW] = np.vstack((conesInput[ConeTypes.YELLOW], conesYellowInSemiCircle))
                
                path = pathPlanner.calculatePathInGlobalFrame(vehiclePosition=pos, vehicleDirection=dir, cones=conesInput) #type: ignore
                if(n==frames-1):
                    print(f"Max Frames Reached ({frames}).")
                    print(f"Finished. NormalCaseCount = {self.pathPlanner.normalCaseCount}" )
                    print(f"Finished. CornerCaseCount = {self.pathPlanner.cornerCaseCount}" )
                                    
                cornerFlags.append(pathPlanner.cornerCaseFlag)
                normalFlags.append(pathPlanner.normalCaseFlag)
                Maskx, Masky = create_semicircle(pos, dir, radius)
                paths.append(path)
                Maskxs.append(Maskx)
                Maskys.append(Masky)
                poss.append(pos)
                blues.append(coneBlueINSemiCircle)
                yellows.append(conesYellowInSemiCircle)
            return paths, Maskxs, Maskys, poss, blues, yellows, cornerFlags, normalFlags
        
        paths, Maskxs, Maskys, poss, blues, yellows, cornerFlags, normalFlags = updatePaths(path, self.simulationParameters.viewRadius)
         
        """
            if n > 20 and distance.euclidean(pos, self.simulationParameters.startPos) < 3.0:
                print(f"Finished at frame {n}")
                break
            
            return paths, Maskxs, Maskys, poss, blues, yellows, cornerFlags, normalFlags
        
        paths, Maskxs, Maskys, poss, blues, yellows, cornerFlags, normalFlags = updatePaths(path, self.simulationParameters.viewRadius)
        path = paths[-1][:]
            """
        # Guard clause in case updatePaths returns empty lists (e.g. invalid start) 
        if not paths:
            print("Simulation failed to generate path steps.")
            return

        def drawframe(n):
            pos1.set_data([poss[n][0]], [poss[n][1]])
            ax2.clear()

            # Ensure we don't crash if path is empty
            if len(paths[n]) > 0:
                path1.set_data(paths[n][:, 0], paths[n][:, 1])
                path2 = ax2.scatter(paths[n][:, 0], paths[n][:, 1], c='black', label='Planned Path')

            pos2 = ax2.scatter(poss[n][0], poss[n][1], c='red', label='Car')
            SC.set_data(Maskxs[n], Maskys[n])

            # Handle empty cone arrrays to prevent scatter plot errors
            if len(blues[n]) > 0:
                left2 = ax2.scatter(blues[n][:,0], blues[n][:,1], c='#7CB9E8', label='Blue Cones')
            else:
                left2 = ax2.scatter([],[], c='#7CB9E8')
                #left2.set_label('Blue Cones')
            if len(yellows[n]) > 0:
                right2 = ax2.scatter(yellows[n][:,0], yellows[n][:,1], c='gold', label='Yellow Cones')
            else:
                right2 = ax2.scatter([],[], c='gold')
                #right2.set_label('Yellow Cones')
            ax2.set_title(f""" frame : {n}\n""")

            # Combine Legends logic
            labels_text = f"n : {n}\n"
            bg_color = 'white'

            if(cornerFlags[n]):
                labels_text += f"cornerFlag = {cornerFlags[n]}\n"
                bg_color = '#ffcccb'    #light red
            elif(normalFlags[n]):
                labels_text += f"normalFlag = {normalFlags[n]}\npath len = {len(paths[n])}"
                bg_color = '#90EE90'    #light green

            # create a dummy artist for the test label in legend
            from matplotlib.lines import Line2D
            status_handle = Line2D([],[], color='none', label=labels_text)
            
            handles, labels = ax2.get_legend_handles_labels()
            legend = ax2.legend(handles =[status_handle, path2, pos2], loc = 'upper right')
            legend = ax2.legend(loc='upper right')
            legend.get_frame().set_facecolor(bg_color)

            #return pos1, pos2, path1, path2, SC, left2, right2

            #path2 = ax2.scatter(paths[n][:,0], paths[n][:,1], c='black')
            #SC.set_data(Maskxs[n], Maskys[n])
            #left2 = ax2.scatter(blues[n][:,0], blues[n][:,1], c='#7CB9E8')
            #right2 = ax2.scatter(yellows[n][:,0], yellows[n][:,1], c='gold')
                
            
            #ax2.set_title(f""" frame : {n}\n""")
            """            
            if(cornerFlags[n]):
                left2.set_label(f"n : {n}\ncornerFlag = {cornerFlags[n]}\n")
                legend = ax2.legend()
                legend.get_frame().set_facecolor('#ffcccb')  # light red
            elif(normalFlags[n]):
                left2.set_label(f"n : {n}\nnormalFlag = {normalFlags[n]}\npath = {len(paths[n])}")
                legend = ax2.legend()
                legend.get_frame().set_facecolor('#90EE90')  # light green
                   """ 
            
            return pos1, pos2, path1, path2, SC, left2, right2
        
        anim = animation.FuncAnimation(fig, drawframe, frames=len(poss), interval=100)
        if(createVideo):
            # self.simulation.append(HTML(anim.to_html5_video()))
            self.simulation.append(HTML(anim.to_jshtml()))
        
        
        

    
    
class SimulationParameters:
    track: Track
    startPos: np.ndarray
    startDir: float
    viewRadius: float
    conesBlueInView: np.ndarray
    conesYellowInView: np.ndarray
    seed: int
    
    
    def __init__(self, track, viewRadius, seed = None) -> None:
        self.track = track
        self.viewRadius = viewRadius
        if seed is not None:
            self.seed = seed
            random.seed(seed)
        randIdx = random.randint(0, len(self.track.x_path)-2)
        self.calcStartPos(randIdx)
        self.calcStartDir(randIdx)
        self.calcConesInView()
        
    
    def calcStartPos(self, randIdx):
        startX = self.track.x_path[randIdx]
        startY = self.track.y_path[randIdx]
        self.startPos = np.array([startX, startY])
        
    def calcStartDir(self, randIdx):
        self.startDir = math.atan2(self.track.y_path[randIdx+1] - self.startPos[1], self.track.x_path[randIdx+1] - self.startPos[0])

    def calcConesInView(self):
        self.conesBlueInView = self.track.cones_blue[is_inside_semicircle(self.startPos, self.startDir, self.viewRadius, self.track.cones_blue)]
        self.conesYellowInView = self.track.cones_yellow[is_inside_semicircle(self.startPos, self.startDir, self.viewRadius, self.track.cones_yellow)]
    
        
        
    
    
    
    
class Track:
    jsonFilePath: str
    x_blue : list[float]
    y_blue : list[float]
    x_yellow : list[float]
    y_yellow : list[float]
    x_path : list[float]
    y_path : list[float]
    cones_blue: np.ndarray
    cones_yellow: np.ndarray
    
    
    def __init__(self, jsonFilePath : str) -> None:
        self.jsonFilePath = jsonFilePath
        self.setConesFromFile(self.jsonFilePath)
        self.generateMidpoints()
        self.cones_blue = np.array(list(zip(self.x_blue, self.y_blue)))
        self.cones_yellow = np.array(list(zip(self.x_yellow, self.y_yellow)))
        
    def setConesFromFile(self, tracks) -> None:
        with open(tracks, 'r') as file:
                json_data = json.load(file)
        json_data["color"][0] = "blue"
        self.x_blue = [json_data["x"][i] for i in range(len(json_data["color"])) if json_data["color"][i] == "blue" ]
        self.y_blue = [json_data["y"][i] for i in range(len(json_data["color"])) if json_data["color"][i] == "blue" ]
        self.x_yellow = [json_data["x"][i] for i in range(len(json_data["color"])) if json_data["color"][i] == "yellow"]
        self.y_yellow = [json_data["y"][i] for i in range(len(json_data["color"])) if json_data["color"][i] == "yellow"]
        self.x_yellow.append(self.x_yellow[0])
        self.y_yellow.append(self.y_yellow[0])
        
    def generateMidpoints(self) -> None:
        x_path, y_path = zip(*[calculateMidpoints(yellow_x, yellow_y,self.x_blue,self.y_blue) for yellow_x, yellow_y in zip(self.x_yellow, self.y_yellow)])
        self.x_path = list(x_path)
        self.y_path = list(y_path)
        for i in range(1, len(self.x_path), 2):
            if len(self.x_path) < len(self.x_blue):
                x_midpoint = (self.x_path[i - 1] + self.x_path[i]) / 2
                y_midpoint = (self.y_path[i - 1] + self.y_path[i]) / 2
                self.x_path.insert(i, x_midpoint)
                self.y_path.insert(i, y_midpoint)
            else:
                break
            
    def plotSample(self) -> None:
        plt.figure(figsize=(10, 6))
        plt.plot(self.x_blue, self.y_blue, marker='o', linestyle='-', color='blue', label='Blue Cones', markersize=4)
        plt.plot(self.x_yellow, self.y_yellow, marker='o', linestyle='-', color='yellow', label='Yellow Cones', markersize=4)
        plt.plot(self.x_path, self.y_path, marker='', linestyle='-', color='black', label='Path')
        plt.show()

    
    
    
    
    
#helper functions            
def findClosestBlue(yellow_x, yellow_y, x_blue, y_blue):
    distances = [distance.euclidean((yellow_x, yellow_y), (blue_x, blue_y)) for blue_x, blue_y in zip(x_blue, y_blue)]
    closest_blue_index = distances.index(min(distances))
    return x_blue[closest_blue_index], y_blue[closest_blue_index]

def calculateMidpoints(yellow_x, yellow_y, x_blue, y_blue):
    division_factors = [1, 2, 3]  # You can add more values if needed
    midpoints = []

    for factor in division_factors:
        closest_blue_x, closest_blue_y = findClosestBlue(yellow_x, yellow_y,x_blue, y_blue)
        midpoint_x = (yellow_x + closest_blue_x) / factor
        midpoint_y = (yellow_y + closest_blue_y) / factor
        midpoints.append((midpoint_x, midpoint_y))

    # Choose the midpoint that is most in the middle
    middle_index = len(midpoints) // 2  # Index of the middle value
    return midpoints[middle_index]

def create_semicircle(center, direction, radius):

    # Calculate the starting and ending angles of the semicircle
    start_angle = direction - np.pi/2  # 90 degrees counter-clockwise from the direction
    end_angle = direction + np.pi/2    # 90 degrees clockwise from the direction

    # Generate angles from start_angle to end_angle
    angles = np.linspace(start_angle, end_angle, 100)

    # Calculate x and y coordinates of the semicircle points
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)
    return x, y

def is_inside_semicircle(center, direction, radius, cones):
    # Calculate the starting and ending angles of the semicircle
    start_angle = direction - np.pi/2   # 90 degrees counter-clockwise from the direction
    end_angle = direction + np.pi/2   # 90 degrees clockwise from the direction

    # Prepare arrays to store results
    angle_within_range = np.zeros(len(cones), dtype=bool)
    distance_within_radius = np.zeros(len(cones), dtype=bool)

    # Iterate over each cone and check conditions
    for i, cone in enumerate(cones):
        # Calculate the vector from the center to the cone
        vector_to_cone = cone - center

        # Calculate the angle between the vector and the x-axis
        angle_to_cone = np.arctan2(vector_to_cone[1], vector_to_cone[0])

        # Check if the angle to the cone is within the range of the semicircle
        angle_within_range[i] = start_angle <= angle_to_cone <= end_angle
        # Check if the distance from the center to the cone is within the radius
        distance_within_radius[i] = np.linalg.norm(vector_to_cone) <= radius
        # if distance_within_radius[i]:
        #     print(angle_to_cone)

    # Return True for cones that satisfy both conditions
    # print(cones[angle_within_range==True])

    # plt.scatter(cones[distance_within_radius==True][:,0], cones[distance_within_radius==True][:,1])
    return angle_within_range & distance_within_radius

