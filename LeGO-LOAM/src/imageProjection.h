#ifndef IMAGEPROJECTION_H
#define IMAGEPROJECTION_H

#include "lego_loam/utility.h"
#include "lego_loam/channel.h"
#include <Eigen/QR>
#include <map>
#include <cmath>


class ImageProjection : public rclcpp::Node {
 public:

  ImageProjection(const std::string &name, Channel<ProjectionOut>& output_channel);

  ~ImageProjection() = default;

  void cloudHandler(const sensor_msgs::msg::PointCloud2::SharedPtr laserCloudMsg);

 private:
  void findStartEndAngle();
  void resetParameters();
  void projectPointCloud();
  void groundRemoval();
  void cloudSegmentation();
  void labelComponents(int row, int col);
  void publishClouds();

  pcl::PointCloud<PointType>::Ptr _laser_cloud_in;

  pcl::PointCloud<PointType>::Ptr _full_cloud;
  pcl::PointCloud<PointType>::Ptr _full_info_cloud;

  pcl::PointCloud<PointType>::Ptr _ground_cloud;
  pcl::PointCloud<PointType>::Ptr _segmented_cloud;
  pcl::PointCloud<PointType>::Ptr _segmented_cloud_pure;
  pcl::PointCloud<PointType>::Ptr _outlier_cloud;
  pcl::PointCloud<PointType>::Ptr _cone_cloud;

  int verticalScans;
  int horizontalScans;
  float angBottom;
  float angResolutionX;
  float angResolutionY;
  float segmentTheta;
  int segmentValidPointNum;
  int segmentValidLineNum;
  int groundScanIndex;
  float sensorMountAngle;

  std::string _lidarPoints;
  std::string _fullCloudProjected;
  std::string _fullCloudInfo;
  std::string _groundCloud;
  std::string _segmentedCloud;
  std::string _coneCloud;
  std::string _segmentedCloudPure;
  std::string _segmentedCloudInfo;
  std::string _outlierCloud;
  std::string _baseLink;

  Channel<ProjectionOut>& _output_channel;

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr subLaserCloud;

  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pubFullCloud;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pubFullInfoCloud;

  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pubGroundCloud;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pubSegmentedCloud;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pubSegmentedCloudPure;
  rclcpp::Publisher<cloud_msgs::msg::CloudInfo>::SharedPtr pubSegmentedCloudInfo;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pubOutlierCloud;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pubConeCloud;


  cloud_msgs::msg::CloudInfo _seg_msg;

  int _label_count;

  Eigen::MatrixXf _range_mat;   // range matrix for range image
  Eigen::MatrixXi _label_mat;   // label matrix for segmentaiton marking
  Eigen::Matrix<int8_t,Eigen::Dynamic,Eigen::Dynamic> _ground_mat;  // ground matrix for ground cloud marking








  struct LUTEntry {
    float centerline_x = 0.0f;   // lateral centre  (cone_cloud x-axis)
    float half_width   = 0.0f;   // half track width (cone_cloud x-axis)
  };

  std::map<float, LUTEntry> _cone_lut;

  // ── 3. LUT tuning parameters — add to class members ──────────

  // How finely to slice the forward axis (metres)
  float lut_resolution          = 0.5f;

  // EMA smoothing weight for LUT updates  [0, 1]
  float lut_ema_alpha           = 0.3f;

  // Max allowed per-update change in half_width (metres) — outlier gate
  float lut_max_width_change    = 0.5f;

  // Tolerance multiplier: nearby-cone window = lut_resolution * multiplier
  float lut_tolerance_multiplier = 2.0f;

  // Maximum physically plausible track half-width (metres)
  float lut_max_track_half_width = 4.0f;

  // Maximum lateral distance a cone may have from the sensor (metres)
  float lut_max_cone_lateral     = 5.0f;

  // Extra margin added to half_width when querying the LUT (metres)
  float lut_filter_margin        = 0.5f;

  // Forward-axis margins around the LUT's covered range (metres)
  float lut_filter_z_margin_before = 1.0f;
  float lut_filter_z_margin_after  = 1.0f;

  // Maximum distance at which we trust cone detections (metres)
  float lut_max_cone_distance    = 30.0f;

  // ── 4. New method declarations — add to class declaration ────

  // Build / update the LUT from the current frame's cone detections.
  void buildConeLUT(const pcl::PointCloud<PointType>::Ptr& cone_cloud);

  // Return a filtered copy of cone_cloud keeping only cones that
  // fall inside the corridor described by _cone_lut.
  // Falls back to returning all cones when the LUT is empty.
  pcl::PointCloud<PointType>::Ptr filterConesWithLUT(
      const pcl::PointCloud<PointType>::Ptr& cone_cloud);


};



#endif  // IMAGEPROJECTION_H
