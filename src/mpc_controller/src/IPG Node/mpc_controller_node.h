#pragma once

#include <rclcpp/rclcpp.hpp>
#include <ackermann_msgs/msg/ackermann_drive_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <rosgraph_msgs/msg/clock.hpp>
#include <Eigen/Dense>

// MPC library headers
#include "../MPC/mpc.h"

/**
 * @brief ROS 2 MPC Controller Node with Isaac Sim Integration
 *
 * Subscribes to Isaac Sim state feedback and publishes Ackermann commands.
 * Implements closed-loop control with integration layer to convert
 * MPC outputs (steering rate, acceleration) to reference commands.
 */
class MPCControllerNode : public rclcpp::Node {
public:
    MPCControllerNode();
    ~MPCControllerNode() = default;

private:
    // ────────────────────────────────────────────────────────────────────
    // MPC SOLVER
    // ────────────────────────────────────────────────────────────────────
    std::unique_ptr<mpc_controller::MPC> mpc_;

    // ────────────────────────────────────────────────────────────────────
    // STATE FEEDBACK (from Isaac Sim)
    // ────────────────────────────────────────────────────────────────────
    // Measured state from /odom
    double v_meas_;        // forward velocity [m/s]
    double x_meas_;        // position x [m]
    double y_meas_;        // position y [m]
    double theta_meas_;    // yaw heading [rad]

    // Measured steering angle from /joint_states
    double delta_meas_;    // steering angle [rad]

    // Control outputs (to be integrated)
    double delta_dot_;     // steering rate [rad/s]
    double a_;             // acceleration [m/s²]

    // ────────────────────────────────────────────────────────────────────
    // REFERENCE COMMANDS (output to Isaac Sim)
    // ────────────────────────────────────────────────────────────────────
    double delta_ref_;     // reference steering angle [rad]
    double v_ref_;         // reference velocity [m/s]

    // ────────────────────────────────────────────────────────────────────
    // TRACK AND PATH STATE
    // ────────────────────────────────────────────────────────────────────
    nav_msgs::msg::Path reference_path_;
    bool has_reference_path_;
    bool track_set_;

    // ────────────────────────────────────────────────────────────────────
    // CONTROL PARAMETERS
    // ────────────────────────────────────────────────────────────────────
    double control_dt_;           // control loop period [s]
    double control_frequency_;    // control frequency [Hz]
    double max_steering_angle_;   // maximum steering angle limit [rad]
    double max_velocity_;         // maximum velocity limit [m/s]

    // ────────────────────────────────────────────────────────────────────
    // ROS 2 INTERFACES
    // ────────────────────────────────────────────────────────────────────
    // Publishers
    rclcpp::Publisher<ackermann_msgs::msg::AckermannDriveStamped>::SharedPtr 
        ackermann_cmd_pub_;

    // Subscribers
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr   odom_sub_;
    rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_states_sub_;
    rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr       reference_path_sub_;
    rclcpp::Subscription<rosgraph_msgs::msg::Clock>::SharedPtr clock_sub_;

    // Timer
    rclcpp::TimerBase::SharedPtr control_timer_;

    // ────────────────────────────────────────────────────────────────────
    // CALLBACKS
    // ────────────────────────────────────────────────────────────────────
    /**
     * @brief Extract position, velocity, and yaw from odometry message
     * Source: Isaac Sim /odom topic
     */
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);

    /**
     * @brief Extract steering angles and compute delta_meas
     * Source: Isaac Sim /joint_states topic
     */
    void jointStatesCallback(const sensor_msgs::msg::JointState::SharedPtr msg);

    /**
     * @brief Store reference path waypoints
     * Source: /path topic
     */
    void pathCallback(const nav_msgs::msg::Path::SharedPtr msg);

    /**
     * @brief Optional: synchronize with simulation clock
     * Source: /clock topic (rosgraph_msgs/Clock)
     */
    void clockCallback(const rosgraph_msgs::msg::Clock::SharedPtr msg);

    // ────────────────────────────────────────────────────────────────────
    // CONTROL LOOP AND INTEGRATION
    // ────────────────────────────────────────────────────────────────────
    /**
     * @brief Main control loop: called at fixed frequency
     * 1. Runs MPC solver with current measured state
     * 2. Applies integration layer
     * 3. Publishes Ackermann command
     */
    void controlLoop();

    /**
     * @brief INTEGRATION LAYER
     * Converts MPC outputs to reference commands with limits applied
     * 
     * Inputs:
     *   - delta_meas, v_meas (current measured state)
     *   - delta_dot, a (MPC outputs)
     *   - control_dt (time step)
     * 
     * Outputs:
     *   - delta_ref, v_ref (clamped reference commands)
     */
    void integrationLayer();

    /**
     * @brief PUBLISHER
     * Sends Ackermann command to Isaac Sim
     * Fills: steering_angle, steering_angle_velocity, speed, acceleration
     */
    void publishAckermannCommand();
};
