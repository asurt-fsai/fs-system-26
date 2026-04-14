#pragma once
// ─────────────────────────────────────────────────────────────────────────────
// Standalone Kinematic Bicycle Simulator for RViz Testing
//
// This node replaces the real car (IPG) for offline development:
//   • Subscribes to /cmd_vel  (acceleration + steering rate from MPC)
//   • Integrates the kinematic bicycle model forward
//   • Publishes /odom so the MPC controller can close the loop
//   • Publishes /reference_path from a CSV file or a parameterised oval track
//
// The MPC controller node and the visualizer node run alongside this node
// using the rviz_test.launch.py file.
// ─────────────────────────────────────────────────────────────────────────────

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <cmath>
#include <string>
#include <vector>
#include <utility>

class BicycleSimulator : public rclcpp::Node {
public:
    BicycleSimulator();

private:
    void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg);
    void simStep();
    void publishOdom();
    void publishTrack();
    bool loadTrackCSV(const std::string& csv_path);
    void generateOvalTrack();

    // Vehicle state
    double x_      = 0.0;
    double y_      = 0.0;
    double theta_  = 0.0;
    double delta_  = 0.0;
    double v_      = 1.0;   // start with small initial speed

    // Latest control from MPC: acceleration + target steering angle
    double cmd_accel_        = 0.0;
    double cmd_delta_target_ = 0.0;

    // Parameters
    double wheelbase_ = 1.575;
    double sim_dt_    = 0.01;   // 100 Hz physics
    double v_max_     = 15.0;
    double delta_max_ = 0.6109;

    // Track generation (oval fallback)
    double track_a_ = 40.0;   // semi-major axis of oval
    double track_b_ = 20.0;   // semi-minor axis of oval
    int    track_n_ = 200;    // number of waypoints

    // CSV track
    std::string track_csv_path_;   // empty → generate oval

    // Loaded track waypoints (from CSV or oval generator)
    std::vector<std::pair<double, double>> track_points_;

    // ROS interfaces
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr      odom_pub_;
    rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr          track_pub_;
    rclcpp::TimerBase::SharedPtr sim_timer_;
    rclcpp::TimerBase::SharedPtr track_timer_;
};
