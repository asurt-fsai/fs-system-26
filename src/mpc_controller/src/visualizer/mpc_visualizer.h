#pragma once
// ─────────────────────────────────────────────────────────────────────────────
// MPC Visualization Node — publishes RViz markers for:
//   • Reference track centerline + boundary walls (offset using track headings)
//   • Track constraint normals at each MPC stage
//   • Vehicle heading arrow
//   • Predicted MPC horizon path (line + spheres)
//   • Vehicle footprint with wheels (wireframe)
//   • Cone markers at track edges
//
// Used by both IPG (real car) and the standalone RViz simulator.
// Subscribes to the same topics the MPC node publishes.
// ─────────────────────────────────────────────────────────────────────────────

#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

class MPCVisualizer : public rclcpp::Node {
public:
    MPCVisualizer();

private:
    // ── Callbacks ─────────────────────────────────────────────────────────
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);
    void pathCallback(const nav_msgs::msg::Path::SharedPtr msg);
    void predictedPathCallback(const nav_msgs::msg::Path::SharedPtr msg);
    void timerCallback();

    // ── Marker builders ───────────────────────────────────────────────────
    void publishTrackMarkers();
    void publishHeadingArrow(const nav_msgs::msg::Odometry& odom);
    void publishVehicleFootprint(const nav_msgs::msg::Odometry& odom);
    void publishPredictedPath();
    void publishTrackConstraints();
    void broadcastTF(const nav_msgs::msg::Odometry& odom);

    // ── Helpers ───────────────────────────────────────────────────────────
    double getYawFromQuat(const geometry_msgs::msg::Quaternion& q) const;
    size_t findClosestIndex(double px, double py) const;

    // ── State ──────────────────────────────────────────────────────────────
    nav_msgs::msg::Odometry::SharedPtr latest_odom_;
    nav_msgs::msg::Path::SharedPtr     reference_path_;
    nav_msgs::msg::Path::SharedPtr     predicted_path_;
    bool has_odom_       = false;
    bool has_ref_path_   = false;
    bool has_pred_path_  = false;

    // Vehicle dimensions (FSAI car)
    double car_length_  = 2.8;     // total length [m]
    double car_width_   = 1.4;     // total width [m]
    double wheelbase_   = 1.575;   // front-to-rear axle [m]
    double track_width_ = 1.5;     // half-width each side (fallback if r_inner/r_outer not set)
    double r_inner_     = 1.5;     // track inner boundary offset from centerline [m]
    double r_outer_     = 1.5;     // track outer boundary offset from centerline [m]
    int    cone_spacing_ = 5;      // place a cone every N waypoints

    // ── ROS interfaces ─────────────────────────────────────────────────────
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr  odom_sub_;
    rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr      ref_path_sub_;
    rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr      pred_path_sub_;

    rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_pub_;
    rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr      heading_pub_;
    rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr      footprint_pub_;
    rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr constraint_pub_;
    rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr pred_viz_pub_;

    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    rclcpp::TimerBase::SharedPtr vis_timer_;
};
