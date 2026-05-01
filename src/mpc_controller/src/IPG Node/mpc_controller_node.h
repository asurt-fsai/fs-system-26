#pragma once

#include <rclcpp/rclcpp.hpp>
#include <ackermann_msgs/msg/ackermann_drive_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <Eigen/Dense>

// MPC library headers
#include "../MPC/mpc.h"

/**
 * @brief ROS 2 MPC Controller Node
 *
 * Bridges ROS 2 topics/services to the mpc_controller::MPC solver.
 */
class MPCControllerNode : public rclcpp::Node {
public:
    MPCControllerNode();
    ~MPCControllerNode() = default;

private:
    // MPC solver (owns the solver and params)
    std::unique_ptr<mpc_controller::MPC> mpc_;

    // Current vehicle state
    mpc_controller::state current_state_;

    // Track path state
    nav_msgs::msg::Path reference_path_;
    bool has_reference_path_;
    bool track_set_;

    // Control timer period [s]
    double control_dt_;

    // ROS 2 interfaces
    rclcpp::Publisher<ackermann_msgs::msg::AckermannDriveStamped>::SharedPtr cmd_vel_pub_;

    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr   odom_sub_;
    rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr       reference_path_sub_;

    rclcpp::TimerBase::SharedPtr control_timer_;

    // Callbacks
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);
    void pathCallback(const nav_msgs::msg::Path::SharedPtr msg);
    void controlLoop();
};
