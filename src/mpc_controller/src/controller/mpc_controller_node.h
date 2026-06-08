#pragma once

#include <rclcpp/rclcpp.hpp>
#include <ackermann_msgs/msg/ackermann_drive_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <Eigen/Dense>
#include <fstream>
#include <string>

#include "../MPC/mpc.h"

class MPCControllerNode : public rclcpp::Node {
public:
    MPCControllerNode();
    ~MPCControllerNode() = default;

private:
    // ── MPC Solver ─────────────────────────────────────────────────────
    std::unique_ptr<mpc_controller::MPC> mpc_;

    // ── Measured state ─────────────────────────────────────────────────
    double x_meas_;                          // position x       [m]
    double y_meas_;                          // position y       [m]
    double theta_meas_;                      // heading          [rad]
    double v_meas_;                          // forward velocity [m/s]
    double delta_meas_;                      // steering angle   [rad]

    // ── MPC outputs ────────────────────────────────────────────────────
    double delta_dot_;   // steering rate  [rad/s]
    double a_;           // acceleration   [m/s²]

    // ── Reference commands (sent to car/sim) ───────────────────────────
    double delta_ref_;   // target steering angle [rad]
    double v_ref_;       // target velocity       [m/s]

    // ── Track state ────────────────────────────────────────────────────
    nav_msgs::msg::Path reference_path_;
    bool has_reference_path_;
    bool track_set_;

    // ── Control parameters ─────────────────────────────────────────────
    double control_dt_;
    double control_frequency_;
    double max_steering_angle_;
    double max_velocity_;
    bool   use_odom_steering_;   // true = read delta from odom.twist.linear.y

    // ── CSV logging ────────────────────────────────────────────────────
    bool          csv_enabled_;
    std::string   csv_lap_dir_;
    std::string   csv_output_path_;
    std::ofstream csv_file_;
    bool          csv_open_ = false;
    void initCsvLogger(const std::string& lap_dir);
    void writeCsvRow(const mpc_controller::state& x0,
                     const mpc_controller::MPCReturn& result);

    // ── ROS 2 publishers ───────────────────────────────────────────────
    rclcpp::Publisher<ackermann_msgs::msg::AckermannDriveStamped>::SharedPtr ackermann_cmd_pub_;
    rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr predicted_path_pub_;

    // ── ROS 2 subscribers ──────────────────────────────────────────────
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr      odom_sub_;
    rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_states_sub_;
    rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr          reference_path_sub_;

    // ── Timer ──────────────────────────────────────────────────────────
    rclcpp::TimerBase::SharedPtr control_timer_;

    // ── Callbacks ──────────────────────────────────────────────────────
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);
    void jointStatesCallback(const sensor_msgs::msg::JointState::SharedPtr msg);
    void pathCallback(const nav_msgs::msg::Path::SharedPtr msg);
    void controlLoop();

    // ── Internal helpers ───────────────────────────────────────────────
    void integrationLayer();
    void publishAckermannCommand();
    void publishPredictedPath(const mpc_controller::MPCReturn& result);
};
