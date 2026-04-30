// Copyright 2013, Ji Zhang, Carnegie Mellon University
// Further contributions copyright (c) 2016, Southwest Research Institute
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice,
//    this list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
// 3. Neither the name of the copyright holder nor the names of its
//    contributors may be used to endorse or promote products derived from this
//    software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.

#include <boost/circular_buffer.hpp>
#include "imageProjection.h"

const std::string PARAM_VERTICAL_SCANS = "laser.num_vertical_scans";
const std::string PARAM_HORIZONTAL_SCANS = "laser.num_horizontal_scans";
const std::string PARAM_ANGLE_BOTTOM = "laser.vertical_angle_bottom";
const std::string PARAM_ANGLE_TOP = "laser.vertical_angle_top";
const std::string PARAM_GROUND_INDEX = "laser.ground_scan_index";
const std::string PARAM_SENSOR_ANGLE = "laser.sensor_mount_angle";
const std::string PARAM_SEGMENT_THETA = "image_projection.segment_theta";
const std::string PARAM_SEGMENT_POINT = "image_projection.segment_valid_point_num";
const std::string PARAM_SEGMENT_LINE = "image_projection.segment_valid_line_num";

const std::string PARAM_LUT_RESOLUTION            = "image_projection.lut_resolution";
const std::string PARAM_LUT_EMA_ALPHA             = "image_projection.lut_ema_alpha";
const std::string PARAM_LUT_MAX_WIDTH_CHANGE      = "image_projection.lut_max_width_change";
const std::string PARAM_LUT_TOLERANCE_MULT        = "image_projection.lut_tolerance_multiplier";
const std::string PARAM_LUT_MAX_TRACK_HALF_WIDTH  = "image_projection.lut_max_track_half_width";
const std::string PARAM_LUT_MAX_CONE_LATERAL      = "image_projection.lut_max_cone_lateral";
const std::string PARAM_LUT_FILTER_MARGIN         = "image_projection.lut_filter_margin";
const std::string PARAM_LUT_FILTER_Z_BEFORE       = "image_projection.lut_filter_z_margin_before";
const std::string PARAM_LUT_FILTER_Z_AFTER        = "image_projection.lut_filter_z_margin_after";
const std::string PARAM_LUT_MAX_CONE_DIST         = "image_projection.lut_max_cone_distance";


ImageProjection::ImageProjection(const std::string &name, Channel<ProjectionOut>& output_channel)
    : Node(name),  _output_channel(output_channel)
{
  /* Handles the projection of LiDAR data into a 2D image plane and segmentation of the ground and obstacles.
  
   Attributes
   ----------
   subLaserCloud : Subscription to raw LiDAR point cloud data.
   pubFullCloud : Publisher for the full point cloud projected into a 2D image plane.
   pubFullInfoCloud : Publisher for the full point cloud with additional information per point.
   pubGroundCloud : Publisher for the detected ground points in the point cloud.
   pubSegmentedCloud : Publisher for the segmented non-ground points in the point cloud.
   pubSegmentedCloudPure : Publisher for the pure segmented non-ground points without additional information.
   pubSegmentedCloudInfo : Publisher for metadata information about the segmented cloud.
   pubOutlierCloud : Publisher for outlier points detected during segmentation.
  
   Methods
   -------
   ImageProjection(const std::string &name, Channel<ProjectionOut>& output_channel) :
       Constructs an ImageProjection object and initializes ROS communication.
       Parameters include the name of the node and a reference to the output channel for processed data.
  
   void resetParameters() :
       Resets and initializes parameters and storage containers used in LiDAR data processing.
  
   void cloudHandler(const sensor_msgs::msg::PointCloud2::SharedPtr laserCloudMsg) :
       Callback function for the LiDAR point cloud subscription. Handles incoming raw point cloud data.
  
   void projectPointCloud() :
       Projects the raw 3D LiDAR point cloud into a 2D image plane based on the LiDAR's intrinsic parameters.
  
   void findStartEndAngle() :
       Calculates the start and end angles of the LiDAR scan to assist in segmenting the point cloud.
  
   void groundRemoval() :
       Segments the ground from the point cloud based on the sensor's mounting angle and the ground's expected slope.
  
   void cloudSegmentation() :
       Segments the non-ground points for further processing, such as object detection and avoidance.
  
   void labelComponents(int row, int col) :
       Labels the components in the segmented cloud to differentiate between distinct objects.
  
   void publishClouds() :
       Publishes various forms of processed point clouds for visualization and further processing.
 */
  
  // Declare Topic Parameters
  this->declare_parameter("topics.lidarPoints", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.fullCloudProjected", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.fullCloudInfo", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.groundCloud", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.segmentedCloud", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.segmentedCloudPure", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.segmentedCloudInfo", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.outlierCloud", rclcpp::PARAMETER_STRING);
  this->declare_parameter("frames.baseLink", rclcpp::PARAMETER_STRING);
  this->declare_parameter("topics.ConeCloud", rclcpp::PARAMETER_STRING);

  // Get Topic Parameters
  this->get_parameter("topics.lidarPoints", _lidarPoints);
  this->get_parameter("topics.fullCloudProjected", _fullCloudProjected);
  this->get_parameter("topics.fullCloudInfo", _fullCloudInfo);
  this->get_parameter("topics.groundCloud", _groundCloud);
  this->get_parameter("topics.segmentedCloud", _segmentedCloud);
  this->get_parameter("topics.segmentedCloudPure", _segmentedCloudPure);
  this->get_parameter("topics.segmentedCloudInfo", _segmentedCloudInfo);
  this->get_parameter("topics.outlierCloud", _outlierCloud);
  this->get_parameter("frames.baseLink", _baseLink);
  this->get_parameter("topics.ConeCloud", _coneCloud);
  
  subLaserCloud = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      _lidarPoints, 1, std::bind(&ImageProjection::cloudHandler, this, std::placeholders::_1));

  pubFullCloud = this->create_publisher<sensor_msgs::msg::PointCloud2>(_fullCloudProjected, 1);
  pubFullInfoCloud = this->create_publisher<sensor_msgs::msg::PointCloud2>(_fullCloudInfo, 1);
  pubGroundCloud = this->create_publisher<sensor_msgs::msg::PointCloud2>(_groundCloud, 1);
  pubSegmentedCloud = this->create_publisher<sensor_msgs::msg::PointCloud2>(_segmentedCloud, 1);
  pubConeCloud = this->create_publisher<sensor_msgs::msg::PointCloud2>(_coneCloud, 1);
  pubSegmentedCloudPure = this->create_publisher<sensor_msgs::msg::PointCloud2>(_segmentedCloudPure, 1);
  pubSegmentedCloudInfo = this->create_publisher<cloud_msgs::msg::CloudInfo>(_segmentedCloudInfo, 1);
  pubOutlierCloud = this->create_publisher<sensor_msgs::msg::PointCloud2>(_outlierCloud, 1);

  // Declare parameters
  this->declare_parameter(PARAM_VERTICAL_SCANS, rclcpp::PARAMETER_INTEGER);
  this->declare_parameter(PARAM_HORIZONTAL_SCANS, rclcpp::PARAMETER_INTEGER);
  this->declare_parameter(PARAM_ANGLE_BOTTOM, rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_ANGLE_TOP, rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_GROUND_INDEX, rclcpp::PARAMETER_INTEGER);
  this->declare_parameter(PARAM_SENSOR_ANGLE, rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_SEGMENT_THETA, rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_SEGMENT_POINT, rclcpp::PARAMETER_INTEGER);
  this->declare_parameter(PARAM_SEGMENT_LINE, rclcpp::PARAMETER_INTEGER);

  float vertical_angle_top;

  // Read parameters
  if (!this->get_parameter(PARAM_VERTICAL_SCANS, verticalScans)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_VERTICAL_SCANS.c_str());
  }
  if (!this->get_parameter(PARAM_HORIZONTAL_SCANS, horizontalScans)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_HORIZONTAL_SCANS.c_str());
  }
  if (!this->get_parameter(PARAM_ANGLE_BOTTOM, angBottom)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_ANGLE_BOTTOM.c_str());
  }
  if (!this->get_parameter(PARAM_ANGLE_TOP, vertical_angle_top)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_ANGLE_TOP.c_str());
  }
  if (!this->get_parameter(PARAM_GROUND_INDEX, groundScanIndex)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s found", PARAM_GROUND_INDEX.c_str());
  }
  if (!this->get_parameter(PARAM_SENSOR_ANGLE, sensorMountAngle)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_SENSOR_ANGLE.c_str());
  }
  if (!this->get_parameter(PARAM_SEGMENT_THETA, segmentTheta)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_SEGMENT_THETA.c_str());
  }
  if (!this->get_parameter(PARAM_SEGMENT_POINT, segmentValidPointNum)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_SEGMENT_POINT.c_str());
  }
  if (!this->get_parameter(PARAM_SEGMENT_LINE, segmentValidLineNum)) {
    RCLCPP_WARN(this->get_logger(), "Parameter %s not found", PARAM_SEGMENT_LINE.c_str());
  }


  // Declare LUT parameters
  this->declare_parameter(PARAM_LUT_RESOLUTION,           rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_EMA_ALPHA,            rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_MAX_WIDTH_CHANGE,     rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_TOLERANCE_MULT,       rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_MAX_TRACK_HALF_WIDTH, rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_MAX_CONE_LATERAL,     rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_FILTER_MARGIN,        rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_FILTER_Z_BEFORE,      rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_FILTER_Z_AFTER,       rclcpp::PARAMETER_DOUBLE);
  this->declare_parameter(PARAM_LUT_MAX_CONE_DIST,        rclcpp::PARAMETER_DOUBLE);
 
  // Read LUT parameters  (fall back to the defaults set in the header if absent)
  double tmp;
  if (this->get_parameter(PARAM_LUT_RESOLUTION, tmp))
      lut_resolution = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_RESOLUTION.c_str(), lut_resolution);
 
  if (this->get_parameter(PARAM_LUT_EMA_ALPHA, tmp))
      lut_ema_alpha = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_EMA_ALPHA.c_str(), lut_ema_alpha);
 
  if (this->get_parameter(PARAM_LUT_MAX_WIDTH_CHANGE, tmp))
      lut_max_width_change = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_MAX_WIDTH_CHANGE.c_str(), lut_max_width_change);
 
  if (this->get_parameter(PARAM_LUT_TOLERANCE_MULT, tmp))
      lut_tolerance_multiplier = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_TOLERANCE_MULT.c_str(), lut_tolerance_multiplier);
 
  if (this->get_parameter(PARAM_LUT_MAX_TRACK_HALF_WIDTH, tmp))
      lut_max_track_half_width = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_MAX_TRACK_HALF_WIDTH.c_str(), lut_max_track_half_width);
 
  if (this->get_parameter(PARAM_LUT_MAX_CONE_LATERAL, tmp))
      lut_max_cone_lateral = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_MAX_CONE_LATERAL.c_str(), lut_max_cone_lateral);
 
  if (this->get_parameter(PARAM_LUT_FILTER_MARGIN, tmp))
      lut_filter_margin = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_FILTER_MARGIN.c_str(), lut_filter_margin);
 
  if (this->get_parameter(PARAM_LUT_FILTER_Z_BEFORE, tmp))
      lut_filter_z_margin_before = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_FILTER_Z_BEFORE.c_str(), lut_filter_z_margin_before);
 
  if (this->get_parameter(PARAM_LUT_FILTER_Z_AFTER, tmp))
      lut_filter_z_margin_after = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_FILTER_Z_AFTER.c_str(), lut_filter_z_margin_after);
 
  if (this->get_parameter(PARAM_LUT_MAX_CONE_DIST, tmp))
      lut_max_cone_distance = static_cast<float>(tmp);
  else
      RCLCPP_WARN(this->get_logger(), "Parameter %s not found, using default %.2f",
                  PARAM_LUT_MAX_CONE_DIST.c_str(), lut_max_cone_distance);
 


  angResolutionX = (M_PI*2) / (horizontalScans);
  angResolutionY = DEG_TO_RAD*(vertical_angle_top - angBottom) / float(verticalScans-1);
  angBottom = -( angBottom - 0.1) * DEG_TO_RAD;
  segmentTheta *= DEG_TO_RAD;
  sensorMountAngle *= DEG_TO_RAD;

  const size_t cloud_size = verticalScans * horizontalScans;

  _laser_cloud_in.reset(new pcl::PointCloud<PointType>());
  _full_cloud.reset(new pcl::PointCloud<PointType>());
  _full_info_cloud.reset(new pcl::PointCloud<PointType>());

  _ground_cloud.reset(new pcl::PointCloud<PointType>());
  _segmented_cloud.reset(new pcl::PointCloud<PointType>());
  _segmented_cloud_pure.reset(new pcl::PointCloud<PointType>());
  _outlier_cloud.reset(new pcl::PointCloud<PointType>());
  _cone_cloud.reset(new pcl::PointCloud<PointType>());

  _full_cloud->points.resize(cloud_size);
  _full_info_cloud->points.resize(cloud_size);
}

void ImageProjection::resetParameters() {

  /* Summary: Resets and initializes parameters and storage containers for processing a new LiDAR scan.

   Extended Description: Prepares for a new LiDAR scan by resetting internal states, clearing point clouds,
   and reinitializing matrices related to scan processing. It fills point clouds with NaN values to denote 
   unassigned points and sets matrices for range, ground detection, and labeling to their default values. 
   This process ensures that the system is ready for a fresh set of LiDAR data, effectively separating 
   the processing of the current scan from any previous scans.

   Parameters
   ----------
   - cloud_size : size_t
       The total number of points that can be stored in the cloud, calculated based on the LiDAR's vertical and horizontal resolution.
   - nanPoint : PointType
       A point filled with NaN values, used to initialize the point clouds.
   - _laser_cloud_in : pcl::PointCloud<PointType>::Ptr
       The input cloud received from the LiDAR sensor, cleared to remove previous scan data.
   - _ground_cloud : pcl::PointCloud<PointType>::Ptr
       Cloud containing ground points, cleared for the new scan.
   - _segmented_cloud : pcl::PointCloud<PointType>::Ptr
       Cloud containing segmented non-ground points, cleared for the new scan.
   - _segmented_cloud_pure : pcl::PointCloud<PointType>::Ptr
       Cloud containing purely segmented points without ground points, cleared for the new scan.
   - _outlier_cloud : pcl::PointCloud<PointType>::Ptr
       Cloud containing outlier points, cleared for the new scan.
   - _range_mat : Eigen::MatrixXf
       Matrix holding the range (distance) information of each point in the scan, reinitialized to maximum float values.
   - _ground_mat : Eigen::MatrixXi
       Matrix indicating whether a point is ground or not, reset to zero.
   - _label_mat : Eigen::MatrixXi
       Matrix used for labeling points in the cloud, reset to zero.
   - _label_count : int
       Counter for the number of labels used in segmentation, reset to 1.
   - _seg_msg : cloud_msgs::msg::CloudInfo
       Data structure to hold information about the segmented cloud, reset for the new scan processing.

   Returns
   -------
   This function updates the internal state of the ImageProjection object to be ready for the next scan processing.
*/

  const size_t cloud_size = verticalScans * horizontalScans;
  PointType nanPoint;
  nanPoint.x = std::numeric_limits<float>::quiet_NaN();
  nanPoint.y = std::numeric_limits<float>::quiet_NaN();
  nanPoint.z = std::numeric_limits<float>::quiet_NaN();

  _laser_cloud_in->clear();
  _ground_cloud->clear();
  _segmented_cloud->clear();
  _segmented_cloud_pure->clear();
  _outlier_cloud->clear();
  _cone_cloud->clear();

  _range_mat.resize(verticalScans, horizontalScans);
  _ground_mat.resize(verticalScans, horizontalScans);
  _label_mat.resize(verticalScans, horizontalScans);

  _range_mat.fill(FLT_MAX);
  _ground_mat.setZero();
  _label_mat.setZero();

  _label_count = 1;

  std::fill(_full_cloud->points.begin(), _full_cloud->points.end(), nanPoint);
  std::fill(_full_info_cloud->points.begin(), _full_info_cloud->points.end(),
            nanPoint);

  _seg_msg.start_ring_index.assign(verticalScans, 0);
  _seg_msg.end_ring_index.assign(verticalScans, 0);

  _seg_msg.segmented_cloud_ground_flag.assign(cloud_size, false);
  _seg_msg.segmented_cloud_col_ind.assign(cloud_size, 0);
  _seg_msg.segmented_cloud_range.assign(cloud_size, 0);
}

void ImageProjection::cloudHandler(
    const sensor_msgs::msg::PointCloud2::SharedPtr laserCloudMsg) {

  /* Summary: Handles the processing of incoming raw LiDAR point cloud data.

   Extended Description: This method is the main processing pipeline for LiDAR point cloud data. 
   It begins by resetting internal parameters to prepare for a new scan. Then, it converts the incoming
   ROS point cloud message to PCL format, removing any NaN points in the process. It calculates the start
   and end angles of the scan, projects the 3D points into a 2D range image, removes ground points, 
   segments the remaining points into meaningful clusters, and finally publishes the processed data for further use.

   Parameters
   ----------
   - laserCloudMsg : sensor_msgs::msg::PointCloud2::SharedPtr
       The incoming LiDAR scan data in ROS point cloud message format.

   Steps
   -----
   1. Reset internal parameters to prepare for new scan data.
   2. Convert ROS message to PCL point cloud and remove NaN points.
   3. Calculate the start and end angles of the LiDAR scan.
   4. Project the 3D LiDAR points into a 2D range image.
   5. Remove ground points from the projected image.
   6. Segment the non-ground points into clusters.
   7. Publish various processed point clouds for visualization and further processing.

   Returns
   -------
   This function processes the input point cloud and publishes the results.
*/
  // Reset parameters
  resetParameters();

  // Copy and remove NAN points
  pcl::fromROSMsg(*laserCloudMsg, *_laser_cloud_in);
  std::vector<int> indices;
  pcl::removeNaNFromPointCloud(*_laser_cloud_in, *_laser_cloud_in, indices);
  _seg_msg.header = laserCloudMsg->header;

  findStartEndAngle();
  // Range image projection
  projectPointCloud();
  // Mark ground points
  groundRemoval();
  // Point cloud segmentation
  cloudSegmentation();
  //publish (optionally)
  publishClouds();
}


void ImageProjection::projectPointCloud() {

  /* Summary: Projects the 3D LiDAR points into a 2D range image.

   Extended Description: This method takes the 3D point cloud data from the LiDAR and projects it onto a 2D plane to 
   create a range image. Each point's position in the image is determined by its vertical and horizontal angles relative
   to the LiDAR sensor. This projection facilitates the subsequent processing steps, such as ground removal and point cloud segmentation,
   by simplifying the data structure and reducing the computational complexity.

   Parameters
   ----------
   - cloudSize : size_t
       The total number of points in the incoming LiDAR point cloud.
   - thisPoint : PointType
       A temporary variable to store the current point being processed.
   - range : float
       The distance from the LiDAR sensor to the point.
   - verticalAngle : float
       The vertical angle of the point relative to the sensor.
   - rowIdn : int
       The row index in the 2D range image for the current point.
   - horizonAngle : float
       The horizontal angle of the point relative to the sensor.
   - columnIdn : int
       The column index in the 2D range image for the current point.
   - index : size_t
       The index of the point in the flattened 2D range image array.

   Steps
   -----
   1. Calculate the range for each point in the cloud.
   2. Determine the vertical and horizontal angles of each point.
   3. Compute the corresponding row and column indices in the 2D range image.
   4. Store the point in the appropriate location in the 2D range image, along with its range as intensity value.

   Returns
   -------
   This function modifies the internal 2D range image representation of the 3D point cloud.
*/
  // range image projection
  const size_t cloudSize = _laser_cloud_in->points.size();

  for (size_t i = 0; i < cloudSize; ++i) {
    PointType thisPoint = _laser_cloud_in->points[i];

    float range = sqrt(thisPoint.x * thisPoint.x +
                       thisPoint.y * thisPoint.y +
                       thisPoint.z * thisPoint.z);

    // find the row and column index in the image for this point
    float verticalAngle = std::asin(thisPoint.z / range);
        //std::atan2(thisPoint.z, sqrt(thisPoint.x * thisPoint.x + thisPoint.y * thisPoint.y));

    int rowIdn = (verticalAngle + angBottom) / angResolutionY;
    if (rowIdn < 0 || rowIdn >= verticalScans) {
      continue;
    }

    float horizonAngle = std::atan2(thisPoint.x, thisPoint.y);

    int columnIdn = -round((horizonAngle - M_PI_2) / angResolutionX) + horizontalScans * 0.5;

    if (columnIdn >= horizontalScans){
      columnIdn -= horizontalScans;
    }

    if (columnIdn < 0 || columnIdn >= horizontalScans){
      continue;
    }

    if (range < 0.1){
      continue;
    }

    _range_mat(rowIdn, columnIdn) = range;

    thisPoint.intensity = (float)rowIdn + (float)columnIdn / 10000.0;

    size_t index = columnIdn + rowIdn * horizontalScans;
    _full_cloud->points[index] = thisPoint;
    // the corresponding range of a point is saved as "intensity"
    _full_info_cloud->points[index] = thisPoint;
    _full_info_cloud->points[index].intensity = range;
  }
}

void ImageProjection::findStartEndAngle() {

  /* Summary: Calculates the start and end orientations of the LiDAR scan.

   Extended Description: This method identifies the starting and ending points of the LiDAR scan based on
   the point cloud data. It calculates the orientations (angles) of the first and last points relative to 
   the LiDAR sensor to determine the overall scan range. These orientations are used in segmenting the point cloud by
   identifying the beginning and end of each scan, which is crucial for accurate segmentation and analysis of the data.

   Parameters
   ----------
   - point : PointType
       A variable to hold the first and last points of the LiDAR scan for calculating orientations.

   Steps
   -----
   1. Calculate the orientation angle for the first point in the point cloud.
   2. Calculate the orientation angle for the last point in the point cloud.
   3. Adjust the end orientation to ensure it represents a complete scan cycle.

   Returns
   -------
   - _seg_msg.start_orientation : float
       The calculated start orientation of the LiDAR scan.
   - _seg_msg.end_orientation : float
       The calculated end orientation of the LiDAR scan, adjusted for continuity.
   - _seg_msg.orientation_diff : float
       The difference in orientation between the start and end of the scan, representing the scan's angular span.

   This function modifies the `start_orientation`, `end_orientation`, and `orientation_diff` fields of the `_seg_msg`.
*/
  // start and end orientation of this cloud
  auto point = _laser_cloud_in->points.front();
  _seg_msg.start_orientation = -std::atan2(point.y, point.x);

  point = _laser_cloud_in->points.back();
  _seg_msg.end_orientation = -std::atan2(point.y, point.x) + 2 * M_PI;

  if (_seg_msg.end_orientation - _seg_msg.start_orientation > 3 * M_PI) {
    _seg_msg.end_orientation -= 2 * M_PI;
  } else if (_seg_msg.end_orientation - _seg_msg.start_orientation < M_PI) {
    _seg_msg.end_orientation += 2 * M_PI;
  }
  _seg_msg.orientation_diff =
      _seg_msg.end_orientation - _seg_msg.start_orientation;
}

void ImageProjection::groundRemoval() {

  /* Summary: Segments the ground points from the LiDAR scan.

   Extended Description: This method analyses the point cloud to identify and segment ground points based on the sensor's
   mounting angle and the geometric properties of the points. It utilizes a vertical angle calculation to differentiate 
   ground points from non-ground points. Points are classified into three categories: -1 for no information, 0 for non-ground, and 1 for ground.
   This classification is crucial for subsequent processing stages, such as obstacle detection and path planning.

   Parameters
   ----------
   - lowerInd, upperInd : int
       Indices for the current point and the point directly above it in the point cloud.
   - dX, dY, dZ : float
       Differences in the x, y, and z coordinates between two vertically adjacent points.
   - vertical_angle : float
       The angle between the vertical axis and the line connecting two vertically adjacent points.

   Returns
   -------
   - _ground_mat : Eigen::MatrixXi
       A matrix indicating whether each point is ground (-1 for no info, 0 for non-ground, 1 for ground).
   - _label_mat : Eigen::MatrixXi
       A matrix used for labeling points during segmentation, where ground points and points without valid information are marked as -1.

   This function updates `_ground_mat` to reflect the ground segmentation and modifies `_label_mat` accordingly.

   Note
   ----
   Ground points are identified based on their vertical angle relative to the sensor mount angle. Points with a vertical angle 
   close to the sensor mount angle are considered ground.
  */
  // _ground_mat
  // -1, no valid info to check if ground of not
  //  0, initial value, after validation, means not ground
  //  1, ground
  for (int j = 0; j < horizontalScans; ++j) {
    for (int i = 0; i < groundScanIndex; ++i) {
      int lowerInd = j + (i)*horizontalScans;
      int upperInd = j + (i + 1) * horizontalScans;

      if (_full_cloud->points[lowerInd].intensity == -1 ||
          _full_cloud->points[upperInd].intensity == -1) {
        // no info to check, invalid points
        _ground_mat(i, j) = -1;
        continue;
      }

      float dX =
          _full_cloud->points[upperInd].x - _full_cloud->points[lowerInd].x;
      float dY =
          _full_cloud->points[upperInd].y - _full_cloud->points[lowerInd].y;
      float dZ =
          _full_cloud->points[upperInd].z - _full_cloud->points[lowerInd].z;

      float vertical_angle = std::atan2(dZ , sqrt(dX * dX + dY * dY + dZ * dZ));

      // TODO: review this change

      if ( (vertical_angle - sensorMountAngle) <= 10 * DEG_TO_RAD) {
        _ground_mat(i, j) = 1;
        _ground_mat(i + 1, j) = 1;
      }
    }
  }
  // extract ground cloud (_ground_mat == 1)
  // mark entry that doesn't need to label (ground and invalid point) for
  // segmentation note that ground remove is from 0~_N_scan-1, need _range_mat
  // for mark label matrix for the 16th scan
  for (int i = 0; i < verticalScans; ++i) {
    for (int j = 0; j < horizontalScans; ++j) {
      if (_ground_mat(i, j) == 1 ||
          _range_mat(i, j) == FLT_MAX) {
        _label_mat(i, j) = -1;
      }
    }
  }

  for (int i = 0; i <= groundScanIndex; ++i) {
    for (int j = 0; j < horizontalScans; ++j) {
      if (_ground_mat(i, j) == 1)
        _ground_cloud->push_back(_full_cloud->points[j + i * horizontalScans]);
    }
  }
}

void ImageProjection::cloudSegmentation() {

  /* Summary: Segments the cloud into ground, segmented non-ground, and outlier points.

   Extended Description: This function segments the LiDAR point cloud into ground points, non-ground points, 
   and outliers based on the previously identified ground matrix and labeling. It iterates through the cloud, 
   labeling components and organizing points into their respective categories for further processing.

   Parameters
   ----------
   - Operates directly on class attributes including _ground_mat, _label_mat, and point cloud data.

   Returns
   -------
   - _seg_msg : Contains metadata about the segmentation, including indices and flags for ground points.
   - _segmented_cloud : pcl::PointCloud<PointType>
       Stores the segmented non-ground points.
   - _segmented_cloud_pure : pcl::PointCloud<PointType>
       Stores the pure segmented non-ground points for visualization.
   - _outlier_cloud : pcl::PointCloud<PointType>
       Stores the outlier points detected during segmentation.
   - _label_mat : Eigen::MatrixXi
       Updated during labeling to reflect the segmentation.

   Note
   ----
   The segmentation process identifies points that are not part of the ground and distinguishes between potentially 
   useful non-ground points and outliers. Outliers are points that do not meet the criteria for being included in the segmentation 
   but are not necessarily noise or erroneous readings.
  */
  // segmentation process
  for (int i = 0; i < verticalScans; ++i)
    for (int j = 0; j < horizontalScans; ++j)
      if (_label_mat(i, j) == 0) labelComponents(i, j);

  int sizeOfSegCloud = 0;
  // extract segmented cloud for lidar odometry
  for (int i = 0; i < verticalScans; ++i) {
    _seg_msg.start_ring_index[i] = sizeOfSegCloud - 1 + 5;

    for (int j = 0; j < horizontalScans; ++j) {
      if (_label_mat(i, j) > 0 || _ground_mat(i, j) == 1) {
        // outliers that will not be used for optimization (always continue)
        if (_label_mat(i, j) == 999999) {
          if (i > groundScanIndex && j % 5 == 0) {
            _outlier_cloud->push_back(
                _full_cloud->points[j + i * horizontalScans]);
            continue;
          } else {
            continue;
          }
        }
        // majority of ground points are skipped
        if (_ground_mat(i, j) == 1) {
          if (j % 5 != 0 && j > 5 && j < horizontalScans - 5) continue;
        }
        // mark ground points so they will not be considered as edge features
        // later
        _seg_msg.segmented_cloud_ground_flag[sizeOfSegCloud] =
            (_ground_mat(i, j) == 1);
        // mark the points' column index for marking occlusion later
        _seg_msg.segmented_cloud_col_ind[sizeOfSegCloud] = j;
        // save range info
        _seg_msg.segmented_cloud_range[sizeOfSegCloud] =
            _range_mat(i, j);
        // save seg cloud
        _segmented_cloud->push_back(_full_cloud->points[j + i * horizontalScans]);
        // size of seg cloud
        ++sizeOfSegCloud;
      }
    }

    _seg_msg.end_ring_index[i] = sizeOfSegCloud - 1 - 5;
  }

  // extract segmented cloud for visualization
  for (int i = 0; i < verticalScans; ++i) {
    for (int j = 0; j < horizontalScans; ++j) {
      if (_label_mat(i, j) > 0 && _label_mat(i, j) != 999999) {
        _segmented_cloud_pure->push_back(
            _full_cloud->points[j + i * horizontalScans]);
        _segmented_cloud_pure->points.back().intensity =
            _label_mat(i, j);
      }
    }
  }



  // Create a map from label to list of points
  std::unordered_map<int, std::vector<PointType>> clusters;
  for (const auto& pt : _segmented_cloud_pure->points) {
      int label = static_cast<int>(pt.intensity);
      clusters[label].push_back(pt);
  }

  // For each cluster, decide if it's a cone
  for (const auto& pair : clusters) {
    const auto& pts = pair.second;

    // RCLCPP_INFO(this->get_logger(),
    //     "Cluster: size=%zu", pts.size());


    if (pts.size() < 7 || pts.size() > 60)
        continue;
    
    // Compute bounding box
    float min_x = pts[0].x, max_x = pts[0].x;
    float min_y = pts[0].y, max_y = pts[0].y;
    float min_z = pts[0].z, max_z = pts[0].z;
    for (const auto& pt : pts) {
        if (pt.x < min_x) min_x = pt.x;
        if (pt.x > max_x) max_x = pt.x;
        if (pt.y < min_y) min_y = pt.y;
        if (pt.y > max_y) max_y = pt.y;
        if (pt.z < min_z) min_z = pt.z;
        if (pt.z > max_z) max_z = pt.z;
    }
    float height = max_z - min_z;
    float width_x = max_x - min_x;
    float width_y = max_y - min_y;
    float width_xy = std::max(width_x, width_y); // approximate diameter

    // Typical cone dimensions (adjust based on your cones)
    if (height < 0.1 || height > 0.5)
        continue;
    if (width_xy < 0.05 || width_xy > 0.4)
        continue;
    
    // Optional: check intensity if cones have reflective tape
    // float avg_intensity = std::accumulate(pts.begin(), pts.end(), 0.0,
    //     [](float sum, const PointType& p){ return sum + p.intensity; }) / pts.size();
    // if (avg_intensity < cone_intensity_threshold) continue;
    
    // Compute centroid
    PointType centroid;
    // Convert from LiDAR frame to camera frame (same as LeGO-LOAM convention)
    float cx = (min_x + max_x) / 2.0;
    float cy = (min_y + max_y) / 2.0;
    float cz = (min_z + max_z) / 2.0;

    centroid.x = cy;   // LiDAR y → Camera x
    centroid.y = cz;   // LiDAR z → Camera y
    centroid.z = cx;   // LiDAR x → Camera z
    centroid.intensity = 0;

    // Reject anything too far away (cones beyond 15m are unreliable)
    float dist = sqrt(centroid.x * centroid.x + centroid.y * centroid.y + centroid.z * centroid.z);
    if (dist > 30.0) continue;

    if (min_z > 0.2f) continue;

    float aspect_xy = std::max(width_x, width_y) / std::min(width_x, width_y);
    if (aspect_xy > 2.0f) continue;  // reject elongated shapes




    // With this PCA elongation check:
    float sxx=0, sxy=0, syy=0;
    for (const auto& pt : pts) {
        float dx = pt.x - cx, dy = pt.y - cy;
        sxx += dx*dx;  sxy += dx*dy;  syy += dy*dy;
    }
    sxx /= pts.size();  sxy /= pts.size();  syy /= pts.size();

    float trace = sxx + syy;
    float det   = sxx*syy - sxy*sxy;
    float disc  = std::max(0.0f, trace*trace/4.0f - det);
    float l1 = trace/2.0f + std::sqrt(disc);
    float l2 = trace/2.0f - std::sqrt(disc);

    if (l2 < 1e-6f) continue;
    float elongation = std::sqrt(l1 / l2);
    if (elongation > 3.0f) continue;  // wall/pole: elongated in one direction





    // Reject if taller than wide by too much (walls, poles)
    if (height / width_xy > 3.0) continue;

    // Better: compute actual radius and check circularity
    float max_radius = 0.0f;
    float min_radius = std::numeric_limits<float>::max();
    int inlier_count = 0;
    float sum_r = 0.0f, sum_r2 = 0.0f;
    for (const auto& pt : pts) {
        float dx = pt.x - cx;
        float dy = pt.y - cy;
        float r = std::sqrt(dx*dx + dy*dy);
        sum_r  += r;
        sum_r2 += r * r;
        max_radius = std::max(max_radius, r);
        min_radius = std::min(min_radius, r);
        if (r < 0.25f) inlier_count++;  // example radius threshold
    }

    if (max_radius < 0.025f || max_radius > 0.2f) continue;
    //if (max_radius / min_radius > 4.0f) continue;  // not circular enough
    if (static_cast<float>(inlier_count) / pts.size() < 0.8f) continue;  // too many outliers from center

    float mean_r = sum_r / pts.size();
    float var_r  = sum_r2 / pts.size() - mean_r * mean_r;
    float std_r  = std::sqrt(std::max(0.0f, var_r));

    //if (mean_r < 0.01f) continue;               // degenerate cluster
    //if (std_r / mean_r > 0.65f) continue;       // too irregular — not cone-like


    _cone_cloud->push_back(centroid);
  }
  // 1. Update the LUT with RAW detections so the horizon can expand
    buildConeLUT(_cone_cloud); 

    // 2. Now filter a copy for the output/mapping
    auto cone_cloud_filtered = filterConesWithLUT(_cone_cloud);
    
    // 3. Assign the filtered cloud to the member variable for publishing
    _cone_cloud = cone_cloud_filtered;

}

void ImageProjection::buildConeLUT(
    const pcl::PointCloud<PointType>::Ptr& cone_cloud)
{
    if (cone_cloud->empty()) return;

    // ── Gate: keep only cones within reasonable bounds ──────
    std::vector<PointType> gated;
    for (const auto& pt : cone_cloud->points) {
        float dist = std::sqrt(pt.x * pt.x + pt.y * pt.y + pt.z * pt.z);
        if (std::abs(pt.x) > lut_max_cone_lateral) continue;  // too far lateral
        if (dist > lut_max_cone_distance)           continue;  // too far away
        gated.push_back(pt);
    }

    if (gated.size() < 2) return;

    // ── Sort by forward distance (z) ─────────────────────────
    std::sort(gated.begin(), gated.end(),
              [](const PointType& a, const PointType& b){
                  return a.z < b.z;
              });

    float z_min = gated.front().z;
    float z_max = gated.back().z;

    // ── Iterate forward-distance slices ──────────────────────
    float tolerance = lut_resolution * lut_tolerance_multiplier;

    for (float z = z_min; z <= z_max + lut_resolution; z += lut_resolution) {
        // Collect cones near this z-slice
        std::vector<float> left_x,  // lateral x > 0  (left side)
                           right_x; // lateral x < 0  (right side)

        for (const auto& pt : gated) {
            if (std::abs(pt.z - z) <= tolerance) {
                if (pt.x > 0.0f) left_x.push_back(pt.x);
                else              right_x.push_back(pt.x);
            }
        }

        if (left_x.empty() || right_x.empty()) continue;

        // Mean of each side
        float x_left  = 0.0f, x_right = 0.0f;
        for (float v : left_x)  x_left  += v;
        for (float v : right_x) x_right += v;
        x_left  /= static_cast<float>(left_x.size());
        x_right /= static_cast<float>(right_x.size());

        float centerline = (x_left + x_right) / 2.0f;
        float half_width  = std::abs(x_left - x_right) / 2.0f;

        // Sanity check
        if (half_width > lut_max_track_half_width) continue;

        // Quantise z to the LUT bucket key
        float key = std::round(z / lut_resolution) * lut_resolution;

        auto it = _cone_lut.find(key);
        if (it != _cone_lut.end()) {
            // Rate-limit: ignore update if width changed too much (outlier)
            if (std::abs(half_width - it->second.half_width)
                    > lut_max_width_change) continue;

            // EMA update
            it->second.centerline_x = lut_ema_alpha * centerline
                                    + (1.0f - lut_ema_alpha) * it->second.centerline_x;
            it->second.half_width   = lut_ema_alpha * half_width
                                    + (1.0f - lut_ema_alpha) * it->second.half_width;
        } else {
            // First observation
            _cone_lut[key] = {centerline, half_width};
        }
    }

    // ── Sliding window: prune stale entries ──────────────────
    // Keep only entries within lut_max_cone_distance of the
    // current cone cluster's median forward position.
    if (!_cone_lut.empty()) {
        // Median forward position of this frame's detections
        std::vector<float> zvals;
        zvals.reserve(gated.size());
        for (const auto& pt : gated) zvals.push_back(pt.z);
        std::nth_element(zvals.begin(),
                         zvals.begin() + zvals.size()/2,
                         zvals.end());
        float z_center = zvals[zvals.size() / 2];

        float z_lo = z_center - lut_max_cone_distance;
        float z_hi = z_center + lut_max_cone_distance;

        for (auto it = _cone_lut.begin(); it != _cone_lut.end(); ) {
            if (it->first < z_lo || it->first > z_hi)
                it = _cone_lut.erase(it);
            else
                ++it;
        }
    }
}

pcl::PointCloud<PointType>::Ptr ImageProjection::filterConesWithLUT(
    const pcl::PointCloud<PointType>::Ptr& cone_cloud)
{
    auto filtered = std::make_shared<pcl::PointCloud<PointType>>();

    // No LUT yet — pass everything through (bootstrap phase)
    bool has_left  = false, has_right = false;
    for (const auto& kv : _cone_lut) {
        if (kv.second.centerline_x + kv.second.half_width > 0.5f) has_left  = true;
        if (kv.second.centerline_x - kv.second.half_width < -0.5f) has_right = true;
    }
    if (!has_left || !has_right) {
        *filtered = *cone_cloud;   // pass through until both sides seen
        return filtered;
    }

    // Sorted LUT keys for fast nearest-key lookup
    std::vector<float> lut_keys;
    lut_keys.reserve(_cone_lut.size());
    for (const auto& kv : _cone_lut) lut_keys.push_back(kv.first);
    // std::map is already sorted, so lut_keys is ascending

    float lut_z_min = lut_keys.front();
    float lut_z_max = lut_keys.back();

    for (const auto& pt : cone_cloud->points) {
        float z = pt.z;  // forward axis

        // Check if this cone is within the LUT's covered forward range
        // (with a small margin on each end)
        if (z < lut_z_min - lut_filter_z_margin_before) continue;
        if (z > lut_z_max + lut_filter_z_margin_after)  continue;

        // Find nearest LUT bucket
        auto it = _cone_lut.lower_bound(z);  // first key >= z

        LUTEntry entry;
        if (it == _cone_lut.end()) {
            entry = std::prev(it)->second;
        } else if (it == _cone_lut.begin()) {
            entry = it->second;
        } else {
            auto prev_it = std::prev(it);
            // Pick whichever bucket key is closer
            entry = (std::abs(it->first - z) < std::abs(prev_it->first - z))
                    ? it->second : prev_it->second;
        }

        // Keep cone if its lateral position is inside the corridor
        float lateral_dist = std::abs(pt.x - entry.centerline_x);
        if (lateral_dist <= entry.half_width + lut_filter_margin) {
            filtered->push_back(pt);
        }
    }

    return filtered;
}

void ImageProjection::labelComponents(int row, int col) {

  /* Summary: Labels connected components in the segmented LiDAR cloud to identify distinct objects.

   Extended Description: This function implements a region growing algorithm to label each point in the segmented cloud. 
   It starts from a seed point and expands to neighboring points based on the similarity criteria determined by the 
   angle threshold `segmentTheta`. Points within this threshold are considered part of the same object and are labeled identically. 
   The algorithm distinguishes between valid segments and outliers, labeling them accordingly for further processing.

   Parameters
   ----------
   - row : int
       The row index of the seed point in the range image.
   - col : int
       The column index of the seed point in the range image.

   - segmentThetaThreshold : float
       Calculated from `segmentTheta`, determines the angular similarity for expanding the segment.
   - lineCountFlag : std::vector<bool>
       Flags to indicate if a row in the range image has been included in the current segment.
   - queue : boost::circular_buffer<Eigen::Vector2i>
       Queue used for the region growing algorithm, stores indices of points to be evaluated.
   - all_pushed : boost::circular_buffer<Eigen::Vector2i>
       Stores all points that have been added to the queue during the segmentation process.
   - neighborIterator : array of Eigen::Vector2i
       Predefined offsets used to iterate over the immediate neighbors of a point in the range image.

   Returns
   -------
   - _label_mat : Eigen::MatrixXi
       Updated with new labels for each point, indicating their membership to a specific segment or marking them as outliers.
   - _label_count : int
       Incremented for each new valid segment identified during the process.

   - _range_mat : Eigen::MatrixXf
       Contains the range (distance) information for each point in the cloud, used to determine point adjacency and similarity.
   - segmentThetaThreshold : float
       The angle threshold used to determine if a neighboring point is part of the same segment.

   Note
   ----
   The function modifies `_label_mat` directly to assign labels to each point, facilitating the segmentation of the cloud into distinct 
   objects based on geometric continuity.
  */

  const float segmentThetaThreshold = tan(segmentTheta);

  std::vector<bool> lineCountFlag(verticalScans, false);
  const size_t cloud_size = verticalScans * horizontalScans;
  using Coord2D = Eigen::Vector2i;
  boost::circular_buffer<Coord2D> queue(cloud_size);
  boost::circular_buffer<Coord2D> all_pushed(cloud_size);

  queue.push_back({ row,col } );
  all_pushed.push_back({ row,col } );

  const Coord2D neighborIterator[4] = {
      {0, -1}, {-1, 0}, {1, 0}, {0, 1}};

  while (queue.size() > 0) {
    // Pop point
    Coord2D fromInd = queue.front();
    queue.pop_front();

    // Mark popped point
    _label_mat(fromInd.x(), fromInd.y()) = _label_count;
    // Loop through all the neighboring grids of popped grid

    for (const auto& iter : neighborIterator) {
      // new index
      int thisIndX = fromInd.x() + iter.x();
      int thisIndY = fromInd.y() + iter.y();
      // index should be within the boundary
      if (thisIndX < 0 || thisIndX >= verticalScans){
        continue;
      }
      // at range image margin (left or right side)
      if (thisIndY < 0){
        thisIndY = horizontalScans - 1;
      }
      if (thisIndY >= horizontalScans){
        thisIndY = 0;
      }
      // prevent infinite loop (caused by put already examined point back)
      if (_label_mat(thisIndX, thisIndY) != 0){
        continue;
      }

      float d1 = std::max(_range_mat(fromInd.x(), fromInd.y()),
                    _range_mat(thisIndX, thisIndY));
      float d2 = std::min(_range_mat(fromInd.x(), fromInd.y()),
                    _range_mat(thisIndX, thisIndY));

      float alpha = (iter.x() == 0) ? angResolutionX : angResolutionY;
      float tang = (d2 * sin(alpha) / (d1 - d2 * cos(alpha)));

      if (tang > segmentThetaThreshold) {
        queue.push_back( {thisIndX, thisIndY } );

        _label_mat(thisIndX, thisIndY) = _label_count;
        lineCountFlag[thisIndX] = true;

        all_pushed.push_back(  {thisIndX, thisIndY } );
      }
    }
  }

  // check if this segment is valid
  bool feasibleSegment = false;
  if (all_pushed.size() >= 30){
    feasibleSegment = true;
  }
  else if (static_cast<int>(all_pushed.size()) >= segmentValidPointNum) {
    int lineCount = 0;
    for (int i = 0; i < verticalScans; ++i) {
      if (lineCountFlag[i] == true) ++lineCount;
    }
    if (lineCount >= segmentValidLineNum) feasibleSegment = true;
  }
  // segment is valid, mark these points
  if (feasibleSegment == true) {
    ++_label_count;
  } else {  // segment is invalid, mark these points
    for (size_t i = 0; i < all_pushed.size(); ++i) {
      _label_mat(all_pushed[i].x(), all_pushed[i].y()) = 999999;
    }
  }
}

void ImageProjection::publishClouds() {

  /* Summary: Publishes various processed point clouds and their associated information.

   Extended Description: This method is responsible for publishing different types of processed LiDAR point clouds, 
   including the full cloud, ground points, segmented cloud, outliers, and more. It checks for subscribers before publishing
   to avoid unnecessary computations. The function also prepares and sends processed data to the next stage in the pipeline 
   through the `_output_channel`.

   Parameters
   ----------
   temp : sensor_msgs::msg::PointCloud2
       A temporary ROS message used for publishing each processed cloud. It is updated with the current header information.
   PublishCloud : Lambda Function
       A lambda function defined within `publishClouds` to streamline the publishing process for different point clouds. 
       It takes a publisher object, a ROS message template, and a point cloud to publish.

   _output_channel : Channel for sending processed output to the next stage.

   Returns
   -------
   - out : ProjectionOut
       An object containing pointers to the outlier cloud, segmented cloud, and the segmented cloud message. 
       This object is sent through the `_output_channel`.

   Publishers
   ----------
   - pubOutlierCloud : Publisher for outlier cloud points.
   - pubSegmentedCloud : Publisher for segmented cloud points.
   - pubFullCloud : Publisher for the complete projected cloud.
   - pubGroundCloud : Publisher for ground points.
   - pubSegmentedCloudPure : Publisher for purely segmented cloud points.
   - pubFullInfoCloud : Publisher for the full cloud with additional info.
   - pubSegmentedCloudInfo : Publisher for segmented cloud metadata.

   Note
   ----
   This function encapsulates the publishing logic for various point clouds and encapsulates the process of preparing data
   for subsequent processing stages.
*/

  sensor_msgs::msg::PointCloud2 temp;
  temp.header.stamp = _seg_msg.header.stamp;
  temp.header.frame_id = _baseLink;

  auto PublishCloud = [](rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub, sensor_msgs::msg::PointCloud2& temp,
                          const pcl::PointCloud<PointType>::Ptr& cloud) {
    if (pub->get_subscription_count() != 0) {
      sensor_msgs::msg::PointCloud2 _temp;
      pcl::toROSMsg(*cloud, _temp);
      _temp.header.stamp = temp.header.stamp;
      _temp.header.frame_id = temp.header.frame_id;
      pub->publish(_temp);
    }
  };

  PublishCloud(pubOutlierCloud, temp, _outlier_cloud);
  PublishCloud(pubSegmentedCloud, temp, _segmented_cloud);
  PublishCloud(pubConeCloud, temp, _cone_cloud);
  PublishCloud(pubFullCloud, temp, _full_cloud);
  PublishCloud(pubGroundCloud, temp, _ground_cloud);
  PublishCloud(pubSegmentedCloudPure, temp, _segmented_cloud_pure);
  PublishCloud(pubFullInfoCloud, temp, _full_info_cloud);

  if (pubSegmentedCloudInfo->get_subscription_count() != 0) {
    pubSegmentedCloudInfo->publish(_seg_msg);
  }

  //--------------------
  ProjectionOut out;
  out.outlier_cloud.reset(new pcl::PointCloud<PointType>());
  out.segmented_cloud.reset(new pcl::PointCloud<PointType>());
  out.cone_cloud.reset(new pcl::PointCloud<PointType>());

  std::swap( out.seg_msg, _seg_msg);
  std::swap(out.outlier_cloud, _outlier_cloud);
  std::swap(out.segmented_cloud, _segmented_cloud);
  std::swap(out.cone_cloud, _cone_cloud);
  _output_channel.send( std::move(out) );
}
