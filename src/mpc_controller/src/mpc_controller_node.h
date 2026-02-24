#pragma once

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>
#include <Eigen/Dense>

#include "mpc_solver.h"
#include "config.h"

/**
 * @brief ROS 2 MPC Controller Node
 * 
 * Integrates the MPC solver with ROS 2 topics and services
 */
class MPCControllerNode : public rclcpp::Node {
public:
    MPCControllerNode();
    ~MPCControllerNode() = default;

private:
    // Configuration
    MPCConfig config_;
    
    // MPC Solver
    std::unique_ptr<MPCSolver> mpc_solver_;
    
    // State tracking
    Eigen::Vector4d current_state_;  // [x, y, theta, delta]
    nav_msgs::msg::Path reference_path_;
    size_t reference_index_;
    bool has_reference_path_;
    
    // ROS 2 interfaces
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr predicted_path_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr debug_pub_;
    
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
    rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr reference_path_sub_;
    
    rclcpp::TimerBase::SharedPtr control_timer_;
    
    // Callbacks
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);
    void pathCallback(const nav_msgs::msg::Path::SharedPtr msg);
    void controlLoop();
    
    // Helpers
    Eigen::MatrixXd getReferenceTrajectory() const;
    void publishPredictedPath(const Eigen::MatrixXd& trajectory);
    void publishDebugInfo(const MPCSolver::SolveInfo& info);
};
