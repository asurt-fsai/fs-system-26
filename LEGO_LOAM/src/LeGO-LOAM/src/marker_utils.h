#ifndef MARKER_UTILS_H
#define MARKER_UTILS_H

#include <visualization_msgs/msg/marker_array.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>

inline visualization_msgs::msg::MarkerArray createMarkerArray(
    const pcl::PointCloud<pcl::PointXYZI>::Ptr& cloud, 
    const std::string& frame_id, 
    const rclcpp::Time& stamp,
    const std::string& ns = "cones",
    bool swap_camera_to_lidar = false,
    float scale = 0.5,
    float r = 1.0, float g = 0.0, float b = 0.0) 
    
{
    visualization_msgs::msg::MarkerArray marker_array;
    visualization_msgs::msg::Marker marker;
    marker.header.frame_id = frame_id;
    marker.header.stamp = stamp;
    marker.ns = ns;
    marker.id = 0;
    marker.type = visualization_msgs::msg::Marker::SPHERE_LIST;
    marker.action = visualization_msgs::msg::Marker::ADD;
    marker.pose.orientation.w = 1.0;
    marker.scale.x = scale;
    marker.scale.y = scale;
    marker.scale.z = scale;
    marker.color.r = r;
    marker.color.g = g;
    marker.color.b = b;
    marker.color.a = 1.0;

    for (const auto& point : cloud->points) {
        geometry_msgs::msg::Point p;
        if (swap_camera_to_lidar) {
            p.x = point.z;  // Camera Z = Lidar Forward
            p.y = point.x;  // Camera X = Lidar Left
            p.z = point.y;  // Camera Y = Lidar Up
        } else {
            p.x = point.x;
            p.y = point.y;
            p.z = point.z;
        }
        marker.points.push_back(p);
    }
    
    // add DELETEALL marker to clear previous markers just in case, though SPHERE_LIST overwrites cleanly
    visualization_msgs::msg::Marker delete_all;
    delete_all.action = 3; // DELETEALL
    marker_array.markers.push_back(delete_all);
    
    marker_array.markers.push_back(marker);
    return marker_array;
}

#endif
