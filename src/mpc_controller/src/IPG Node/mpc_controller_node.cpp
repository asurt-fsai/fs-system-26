#include "mpc_controller_node.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include <geometry_msgs/msg/pose_stamped.hpp>

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

    // ─── MPC solver (1 SQP iter, reset after 5 consecutive failures) ────
    mpc_ = std::make_unique<mpc_controller::MPC>(
        1 /*n_sqp*/, 5 /*n_reset*/, 1.0 /*sqp_mix*/, control_dt_, paths);

    current_state_.setZero();

    // ─── Publishers ─────────────────────────────────────────────────────
    cmd_vel_pub_ = create_publisher<geometry_msgs::msg::Twist>(
        "/cmd_vel", rclcpp::QoS(10));
    predicted_path_pub_ = create_publisher<nav_msgs::msg::Path>(
        "/mpc/predicted_path", rclcpp::QoS(10));
    debug_pub_ = create_publisher<std_msgs::msg::Float32MultiArray>(
        "/mpc/debug", rclcpp::QoS(10));

    // ─── Subscribers ────────────────────────────────────────────────────
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        "/odom", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::odomCallback, this, std::placeholders::_1));

    reference_path_sub_ = create_subscription<nav_msgs::msg::Path>(
        "/reference_path", rclcpp::QoS(10),
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
    // delta is not directly observable; it is maintained by the solver.
}

void MPCControllerNode::pathCallback(const nav_msgs::msg::Path::SharedPtr msg)
{
    if (msg->poses.empty()) return;
    reference_path_ = *msg;
    has_reference_path_ = true;
    track_set_ = false;  // Trigger spline re-fit on next control cycle
}

void MPCControllerNode::controlLoop()
{
    if (!has_reference_path_) return;

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
    }

    try {
        mpc_controller::state x0 = current_state_;
        mpc_controller::MPCReturn result = mpc_->runMPC(x0);

        // Publish first optimal control: acceleration + steering rate
        geometry_msgs::msg::Twist twist;
        twist.linear.x  = result.u0.D_dot;
        twist.angular.z = result.u0.delta_dot;
        cmd_vel_pub_->publish(twist);

        // Publish full MPC horizon path
        publishPredictedPath(result.mpc_horizon);

        // Publish compute time for monitoring
        std_msgs::msg::Float32MultiArray dbg;
        dbg.data = {static_cast<float>(result.time_total)};
        debug_pub_->publish(dbg);

    } catch (const std::exception& e) {
        RCLCPP_ERROR(get_logger(), "MPC solve error: %s", e.what());
    }
}

void MPCControllerNode::publishPredictedPath(
    const std::array<mpc_controller::OptVariables, N+1>& horizon)
{
    nav_msgs::msg::Path path_msg;
    path_msg.header.frame_id = "map";
    path_msg.header.stamp    = now();

    for (int i = 0; i <= N; ++i) {
        geometry_msgs::msg::PoseStamped ps;
        ps.header = path_msg.header;
        ps.pose.position.x = horizon[i].xk.x;
        ps.pose.position.y = horizon[i].xk.y;

        tf2::Quaternion q;
        q.setRPY(0, 0, horizon[i].xk.theta);
        ps.pose.orientation = tf2::toMsg(q);
        path_msg.poses.push_back(ps);
    }
    predicted_path_pub_->publish(path_msg);
}

int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MPCControllerNode>());
    rclcpp::shutdown();
    return 0;
}
