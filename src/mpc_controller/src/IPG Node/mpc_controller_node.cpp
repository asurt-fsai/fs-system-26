#include "mpc_controller_node.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include <algorithm>

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// Default JSON parameter-file paths (override via ROS2 node parameters)
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
static const char* DFL_MODEL  = "params/model.json";
static const char* DFL_COSTS  = "params/cost.json";
static const char* DFL_BOUNDS = "params/bounds.json";
static const char* DFL_NORM   = "params/normalization.json";

MPCControllerNode::MPCControllerNode()
    : Node("mpc_controller"),
      has_reference_path_(false),
      track_set_(false),
      control_dt_(0.05)   // 20 Hz
{
    // ─── ROS2 parameters ────────────────────────────────────────────────
    declare_parameter("model_path",  DFL_MODEL);
    declare_parameter("costs_path",  DFL_COSTS);
    declare_parameter("bounds_path", DFL_BOUNDS);
    declare_parameter("norm_path",   DFL_NORM);
    declare_parameter("control_dt",  control_dt_);

    mpc_controller::PathToJson paths{
        get_parameter("model_path").as_string(),
        get_parameter("bounds_path").as_string(),
        get_parameter("costs_path").as_string(),
        get_parameter("norm_path").as_string()
    };
    control_dt_ = get_parameter("control_dt").as_double();

    // ─── MPC solver (3 SQP iters, reset after 5 consecutive failures) ────
    mpc_ = std::make_unique<mpc_controller::MPC>(
        3 /*n_sqp*/, 5 /*n_reset*/, 1.0 /*sqp_mix*/, control_dt_, paths);

    current_state_.setZero();

    // ─── Publisher: acceleration + steering angle ─────────────────────
    cmd_vel_pub_ = create_publisher<ackermann_msgs::msg::AckermannDriveStamped>(
        "/action", rclcpp::QoS(10));

    // ─── Subscribers ────────────────────────────────────────────────────
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        "/odom", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::odomCallback, this, std::placeholders::_1));

    reference_path_sub_ = create_subscription<nav_msgs::msg::Path>(
        "/path", rclcpp::QoS(10).transient_local(),
        std::bind(&MPCControllerNode::pathCallback, this, std::placeholders::_1));

    // ─── Control-loop timer ─────────────────────────────────────────────
    using ns = std::chrono::nanoseconds;
    control_timer_ = create_wall_timer(
        std::chrono::duration_cast<ns>(std::chrono::duration<double>(control_dt_)),
        std::bind(&MPCControllerNode::controlLoop, this));

    RCLCPP_INFO(get_logger(), "MPC Controller started (dt=%.3fs)", control_dt_);
}

void MPCControllerNode::odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    const auto& pos = msg->pose.pose.position;
    const auto& ori = msg->pose.pose.orientation;

    tf2::Quaternion q(ori.x, ori.y, ori.z, ori.w);
    double roll, pitch, yaw;
    tf2::Matrix3x3(q).getRPY(roll, pitch, yaw);

    current_state_.x     = pos.x;
    current_state_.y     = pos.y;
    current_state_.theta = yaw;
    current_state_.v     = msg->twist.twist.linear.x;
    current_state_.delta = msg->twist.twist.linear.y;  // steering angle from simulator
}

void MPCControllerNode::pathCallback(const nav_msgs::msg::Path::SharedPtr msg)
{
    if (msg->poses.empty()) return;
    reference_path_ = *msg;
    has_reference_path_ = true;
    track_set_ = false;  // Trigger spline re-fit on next control cycle
    RCLCPP_INFO(get_logger(), "Received reference path with %zu waypoints", msg->poses.size());
}

void MPCControllerNode::controlLoop()
{
    if (!has_reference_path_) {
        static int warn_count = 0;
        if (warn_count++ % 100 == 0)
            RCLCPP_WARN(get_logger(), "Waiting for /path...");
        return;
    }

    // Upload track spline once per new path
    if (!track_set_) {
        const size_t n = reference_path_.poses.size();
        Eigen::VectorXd X(n), Y(n);
        for (size_t i = 0; i < n; ++i) {
            X(i) = reference_path_.poses[i].pose.position.x;
            Y(i) = reference_path_.poses[i].pose.position.y;
        }
        mpc_->setTrack(X, Y);
        track_set_ = true;
        RCLCPP_INFO(get_logger(), "Track spline fit from %zu waypoints", n);
    }

    try {
        mpc_controller::state x0 = current_state_;
        mpc_controller::MPCReturn result = mpc_->runMPC(x0);

        // Compute the target steering angle: current δ + δ̇ * dt
        const double target_delta = std::clamp(
            x0.delta + result.u0.delta_dot * control_dt_,
            -0.6109, 0.6109);  // clamp to steering limits

        // Publish: acceleration + steering angle
        ackermann_msgs::msg::AckermannDriveStamped drive_msg;
        drive_msg.drive.acceleration = result.u0.D_dot;
        drive_msg.drive.steering_angle = target_delta;
        cmd_vel_pub_->publish(drive_msg);

        // Log periodically (~1 Hz at 20 Hz control rate)
        static int log_count = 0;
        if (log_count++ % 20 == 0) {
            RCLCPP_INFO(get_logger(),
                "MPC: x0=(%.2f,%.2f) θ=%.2f δ=%.3f v=%.2f → a=%.3f δ_cmd=%.3f  err=%.2fm t=%.1fms",
                x0.x, x0.y, x0.theta, x0.delta, x0.v,
                result.u0.D_dot, target_delta,
                result.lateral_error, result.time_total * 1000.0);
        }

    } catch (const std::exception& e) {
        RCLCPP_ERROR(get_logger(), "MPC solve error: %s", e.what());
    }
}

int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MPCControllerNode>());
    rclcpp::shutdown();
    return 0;
}
