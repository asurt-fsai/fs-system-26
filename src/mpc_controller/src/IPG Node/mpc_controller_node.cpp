#include "mpc_controller_node.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include <algorithm>
#include <cmath>

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// Default JSON parameter-file paths
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
static const char* DFL_MODEL  = "params/model.json";
static const char* DFL_COSTS  = "params/cost.json";
static const char* DFL_BOUNDS = "params/bounds.json";
static const char* DFL_NORM   = "params/normalization.json";

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// CONSTRUCTOR
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
MPCControllerNode::MPCControllerNode()
    : Node("mpc_controller"),
      v_meas_(0.0), x_meas_(0.0), y_meas_(0.0), theta_meas_(0.0),
      delta_meas_(0.0), delta_dot_(0.0), a_(0.0),
      delta_ref_(0.0), v_ref_(0.0),
      has_reference_path_(false), track_set_(false),
      control_dt_(0.01), control_frequency_(100.0),
      max_steering_angle_(0.6109), max_velocity_(15.0)
{
    // ─── ROS 2 PARAMETERS ───────────────────────────────────────────────
    declare_parameter("model_path",       DFL_MODEL);
    declare_parameter("costs_path",       DFL_COSTS);
    declare_parameter("bounds_path",      DFL_BOUNDS);
    declare_parameter("norm_path",        DFL_NORM);
    declare_parameter("control_frequency", control_frequency_);
    declare_parameter("max_steering_angle", max_steering_angle_);
    declare_parameter("max_velocity",       max_velocity_);

    mpc_controller::PathToJson paths{
        get_parameter("model_path").as_string(),
        get_parameter("bounds_path").as_string(),
        get_parameter("costs_path").as_string(),
        get_parameter("norm_path").as_string()
    };

    control_frequency_ = get_parameter("control_frequency").as_double();
    max_steering_angle_ = get_parameter("max_steering_angle").as_double();
    max_velocity_ = get_parameter("max_velocity").as_double();
    control_dt_ = 1.0 / control_frequency_;

    // ─── MPC SOLVER ─────────────────────────────────────────────────────
    // (3 SQP iters, reset after 5 consecutive failures)
    mpc_ = std::make_unique<mpc_controller::MPC>(
        3 /*n_sqp*/, 5 /*n_reset*/, 1.0 /*sqp_mix*/, control_dt_, paths);

    // ─── ROS 2 PUBLISHER: Ackermann Command ─────────────────────────────
    ackermann_cmd_pub_ = 
        create_publisher<ackermann_msgs::msg::AckermannDriveStamped>(
            "/ackermann_cmd", rclcpp::QoS(10));

    // ─── ROS 2 SUBSCRIBERS: State Feedback from Isaac Sim ────────────────
    // Odometry: position, velocity, heading
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        "/odom", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::odomCallback, this, std::placeholders::_1));

    // Joint states: steering angles of front wheels
    joint_states_sub_ = create_subscription<sensor_msgs::msg::JointState>(
        "/joint_states", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::jointStatesCallback, this, std::placeholders::_1));

    // Reference path: trajectory waypoints
    reference_path_sub_ = create_subscription<nav_msgs::msg::Path>(
        "/path", rclcpp::QoS(10).transient_local(),
        std::bind(&MPCControllerNode::pathCallback, this, std::placeholders::_1));

    // Simulation clock (optional, for time synchronization)
    clock_sub_ = create_subscription<rosgraph_msgs::msg::Clock>(
        "/clock", rclcpp::QoS(1),
        std::bind(&MPCControllerNode::clockCallback, this, std::placeholders::_1));

    // ─── CONTROL TIMER ──────────────────────────────────────────────────
    using ns = std::chrono::nanoseconds;
    control_timer_ = create_wall_timer(
        std::chrono::duration_cast<ns>(std::chrono::duration<double>(control_dt_)),
        std::bind(&MPCControllerNode::controlLoop, this));

    RCLCPP_INFO(get_logger(), 
        "MPC Controller (Isaac Sim) started: f=%.0f Hz, max_δ=%.4f rad, max_v=%.1f m/s",
        control_frequency_, max_steering_angle_, max_velocity_);
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// ROS INTERFACE: ODOMETRY CALLBACK
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    // Extract position
    x_meas_ = msg->pose.pose.position.x;
    y_meas_ = msg->pose.pose.position.y;

    // Extract yaw from quaternion
    const auto& ori = msg->pose.pose.orientation;
    tf2::Quaternion q(ori.x, ori.y, ori.z, ori.w);
    double roll, pitch;
    tf2::Matrix3x3(q).getRPY(roll, pitch, theta_meas_);

    // Extract forward velocity
    v_meas_ = msg->twist.twist.linear.x;
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// ROS INTERFACE: JOINT STATES CALLBACK
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::jointStatesCallback(const sensor_msgs::msg::JointState::SharedPtr msg)
{
    // Extract steering angles from front-left and front-right wheels
    // Common naming conventions in Isaac Sim:
    //   "front_left_wheel_joint" and "front_right_wheel_joint"
    // or "steering_left_joint" and "steering_right_joint"
    
    double delta_left = 0.0, delta_right = 0.0;
    int delta_left_idx = -1, delta_right_idx = -1;

    for (size_t i = 0; i < msg->name.size(); ++i) {
        const auto& joint_name = msg->name[i];
        
        // Look for steering joint names (adjust to match your Isaac Sim config)
        if (joint_name.find("steering") != std::string::npos ||
            joint_name.find("front_left") != std::string::npos) {
            delta_left_idx = i;
        }
        if (joint_name.find("steering") != std::string::npos ||
            joint_name.find("front_right") != std::string::npos) {
            delta_right_idx = i;
        }
    }

    // Compute mean steering angle
    if (delta_left_idx >= 0 && delta_left_idx < (int)msg->position.size()) {
        delta_left = msg->position[delta_left_idx];
    }
    if (delta_right_idx >= 0 && delta_right_idx < (int)msg->position.size()) {
        delta_right = msg->position[delta_right_idx];
    }

    delta_meas_ = (delta_left + delta_right) / 2.0;
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// ROS INTERFACE: PATH CALLBACK
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::pathCallback(const nav_msgs::msg::Path::SharedPtr msg)
{
    if (msg->poses.empty()) return;
    
    reference_path_ = *msg;
    has_reference_path_ = true;
    track_set_ = false;  // Trigger spline re-fit on next control cycle
    
    RCLCPP_INFO(get_logger(), "Received reference path: %zu waypoints", msg->poses.size());
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// ROS INTERFACE: CLOCK CALLBACK (Optional)
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::clockCallback(const rosgraph_msgs::msg::Clock::SharedPtr msg)
{
    // Optional: use simulation clock for time-synchronized control
    // Currently not used, but available for future synchronization
    (void)msg;  // suppress unused warning
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// MAIN CONTROL LOOP
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::controlLoop()
{
    // ─── PRE-CONDITION: Wait for reference path ────────────────────────
    if (!has_reference_path_) {
        static int warn_count = 0;
        if (warn_count++ % 100 == 0)
            RCLCPP_WARN(get_logger(), "Waiting for /path reference trajectory...");
        return;
    }

    // ─── SETUP: Fit track spline once per new path ─────────────────────
    if (!track_set_) {
        const size_t n = reference_path_.poses.size();
        Eigen::VectorXd X(n), Y(n);
        for (size_t i = 0; i < n; ++i) {
            X(i) = reference_path_.poses[i].pose.position.x;
            Y(i) = reference_path_.poses[i].pose.position.y;
        }
        mpc_->setTrack(X, Y);
        track_set_ = true;
        RCLCPP_INFO(get_logger(), "Track spline fitted from %zu waypoints", n);
    }

    try {
        // ───────────────────────────────────────────────────────────────
        // MPC CALL: Optimize with current measured state
        // ───────────────────────────────────────────────────────────────
        mpc_controller::state x0;
        x0.x     = x_meas_;
        x0.y     = y_meas_;
        x0.theta = theta_meas_;
        x0.v     = v_meas_;
        x0.delta = delta_meas_;

        mpc_controller::MPCReturn result = mpc_->runMPC(x0);

        // Extract MPC outputs
        delta_dot_ = result.u0.delta_dot;      // steering rate [rad/s]
        a_ = result.u0.D_dot;                  // acceleration [m/s²]

        // ───────────────────────────────────────────────────────────────
        // INTEGRATION LAYER: Convert rates to reference commands with limits
        // ───────────────────────────────────────────────────────────────
        integrationLayer();

        // ───────────────────────────────────────────────────────────────
        // PUBLISHER: Send Ackermann command to Isaac Sim
        // ───────────────────────────────────────────────────────────────
        publishAckermannCommand();

        // ───────────────────────────────────────────────────────────────
        // DIAGNOSTICS: Log periodically
        // ───────────────────────────────────────────────────────────────
        static int log_count = 0;
        if (log_count++ % (int)control_frequency_ == 0) {  // Log @ ~1 Hz
            RCLCPP_INFO(get_logger(),
                "[MPC-Isaac] meas: (x=%.2f, y=%.2f, θ=%.2f°, v=%.2f, δ=%.3f) "
                "mpc: (a=%.3f, δ̇=%.3f) ref: (v_ref=%.2f, δ_ref=%.3f) err=%.2fm t=%.1fms",
                x_meas_, y_meas_, theta_meas_ * 180.0 / M_PI, v_meas_, delta_meas_,
                a_, delta_dot_, v_ref_, delta_ref_,
                result.lateral_error, result.time_total * 1000.0);
        }

    } catch (const std::exception& e) {
        RCLCPP_ERROR(get_logger(), "MPC solve error: %s", e.what());
    }
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// INTEGRATION LAYER
// Convert MPC outputs (rates) to reference commands (absolute values) with limits
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::integrationLayer()
{
    // ─── STEERING ANGLE INTEGRATION ──────────────────────────────────────
    // delta_ref = delta_meas + delta_dot * dt
    delta_ref_ = delta_meas_ + delta_dot_ * control_dt_;
    
    // Clamp to steering limits
    delta_ref_ = std::clamp(delta_ref_, -max_steering_angle_, max_steering_angle_);

    // ─── VELOCITY INTEGRATION ───────────────────────────────────────────
    // v_ref = v_meas + a * dt
    v_ref_ = v_meas_ + a_ * control_dt_;
    
    // Clamp to velocity limits
    v_ref_ = std::clamp(v_ref_, 0.0, max_velocity_);
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// PUBLISHER: Ackermann Command
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::publishAckermannCommand()
{
    ackermann_msgs::msg::AckermannDriveStamped cmd;
    
    // Timestamp
    cmd.header.stamp = now();
    cmd.header.frame_id = "base_link";

    // ─── Control commands ────────────────────────────────────────────────
    cmd.drive.steering_angle = delta_ref_;                // reference steering [rad]
    cmd.drive.steering_angle_velocity = std::abs(delta_dot_);  // steering rate [rad/s]
    cmd.drive.speed = v_ref_;                             // reference speed [m/s]
    cmd.drive.acceleration = a_;                          // acceleration [m/s²]

    // Publish
    ackermann_cmd_pub_->publish(cmd);
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// MAIN
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MPCControllerNode>());
    rclcpp::shutdown();
    return 0;
}
