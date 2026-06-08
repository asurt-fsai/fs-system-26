#include "mpc_controller_node.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <filesystem>
#include <sys/stat.h>

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// CONSTRUCTOR
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
MPCControllerNode::MPCControllerNode()
    : Node("mpc_controller"),
      x_meas_(0.0), y_meas_(0.0), theta_meas_(0.0),
      v_meas_(0.0), delta_meas_(0.0),
      delta_dot_(0.0), a_(0.0),
      delta_ref_(0.0), v_ref_(0.0),
      has_reference_path_(false), track_set_(false),
      control_dt_(0.05), control_frequency_(20.0),
      max_steering_angle_(0.6109), max_velocity_(15.0),
      use_odom_steering_(true)
{
    // ─── ROS 2 PARAMETERS ───────────────────────────────────────────────
    declare_parameter("model_path",         std::string("params/model.json"));
    declare_parameter("costs_path",         std::string("params/cost.json"));
    declare_parameter("bounds_path",        std::string("params/bounds.json"));
    declare_parameter("norm_path",          std::string("params/normalization.json"));
    declare_parameter("control_frequency",  control_frequency_);
    declare_parameter("max_steering_angle", max_steering_angle_);
    declare_parameter("max_velocity",       max_velocity_);
    declare_parameter("use_odom_steering",  use_odom_steering_);
    declare_parameter("csv_enabled",        true);
    declare_parameter("csv_lap_dir",        std::string("/tmp/lap_tests"));

    mpc_controller::PathToJson paths{
        get_parameter("model_path").as_string(),
        get_parameter("bounds_path").as_string(),
        get_parameter("costs_path").as_string(),
        get_parameter("norm_path").as_string()
    };

    control_frequency_  = get_parameter("control_frequency").as_double();
    max_steering_angle_ = get_parameter("max_steering_angle").as_double();
    max_velocity_       = get_parameter("max_velocity").as_double();
    control_dt_         = 1.0 / control_frequency_;
    use_odom_steering_  = get_parameter("use_odom_steering").as_bool();
    csv_enabled_        = get_parameter("csv_enabled").as_bool();
    csv_lap_dir_        = get_parameter("csv_lap_dir").as_string();

    if (csv_enabled_) {
        initCsvLogger(csv_lap_dir_);
    }

    // ─── MPC SOLVER ─────────────────────────────────────────────────────
    mpc_ = std::make_unique<mpc_controller::MPC>(
        3 /*n_sqp*/, 5 /*n_reset*/, 1.0 /*sqp_mix*/, control_dt_, paths);

    // ─── PUBLISHERS ─────────────────────────────────────────────────────
    ackermann_cmd_pub_ =
        create_publisher<ackermann_msgs::msg::AckermannDriveStamped>(
            "/ackermann_cmd", rclcpp::QoS(10));

    predicted_path_pub_ = create_publisher<nav_msgs::msg::Path>(
        "/mpc/predicted_path", rclcpp::QoS(10));

    // ─── SUBSCRIBERS ────────────────────────────────────────────────────
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        "/odom", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::odomCallback, this, std::placeholders::_1));

    // Joint states: real car steering feedback (when use_odom_steering=false)
    joint_states_sub_ = create_subscription<sensor_msgs::msg::JointState>(
        "/joint_states", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::jointStatesCallback, this, std::placeholders::_1));

    // Track centerline arrives via /path (published by bicycle sim or nav stack)
    reference_path_sub_ = create_subscription<nav_msgs::msg::Path>(
        "/path", rclcpp::QoS(10).transient_local(),
        std::bind(&MPCControllerNode::pathCallback, this, std::placeholders::_1));

    // ─── CONTROL TIMER ──────────────────────────────────────────────────
    using ns = std::chrono::nanoseconds;
    control_timer_ = create_wall_timer(
        std::chrono::duration_cast<ns>(std::chrono::duration<double>(control_dt_)),
        std::bind(&MPCControllerNode::controlLoop, this));

    RCLCPP_INFO(get_logger(),
        "MPC Controller started: f=%.0f Hz, max_δ=%.4f rad, max_v=%.1f m/s",
        control_frequency_, max_steering_angle_, max_velocity_);
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// ODOMETRY CALLBACK  — position, heading, velocity, (optionally) steering
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    x_meas_ = msg->pose.pose.position.x;
    y_meas_ = msg->pose.pose.position.y;
    v_meas_ = msg->twist.twist.linear.x;

    const auto& ori = msg->pose.pose.orientation;
    tf2::Quaternion q(ori.x, ori.y, ori.z, ori.w);
    double roll, pitch;
    tf2::Matrix3x3(q).getRPY(roll, pitch, theta_meas_);

    // Bicycle simulator encodes steering angle in twist.linear.y
    if (use_odom_steering_) {
        delta_meas_ = msg->twist.twist.linear.y;
    }
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// JOINT STATES CALLBACK — real car steering feedback (not used in sim mode)
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::jointStatesCallback(const sensor_msgs::msg::JointState::SharedPtr msg)
{
    if (use_odom_steering_) return;   // bicycle sim mode uses odom instead

    double delta_sum = 0.0;
    int count = 0;
    for (size_t i = 0; i < msg->name.size(); ++i) {
        const auto& name = msg->name[i];
        if ((name.find("steering") != std::string::npos ||
             name.find("front") != std::string::npos) &&
             i < msg->position.size()) {
            delta_sum += msg->position[i];
            ++count;
        }
    }
    if (count > 0) {
        delta_meas_ = delta_sum / count;
    }
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// PATH CALLBACK — receives track centerline from /path topic
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::pathCallback(const nav_msgs::msg::Path::SharedPtr msg)
{
    if (msg->poses.empty()) return;
    reference_path_     = *msg;
    has_reference_path_ = true;
    track_set_          = false;  // trigger spline re-fit
    RCLCPP_INFO(get_logger(), "Received reference path: %zu waypoints", msg->poses.size());
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// MAIN CONTROL LOOP — runs at control_frequency Hz
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::controlLoop()
{
    if (!has_reference_path_) {
        static int warn_count = 0;
        if (warn_count++ % 100 == 0)
            RCLCPP_WARN(get_logger(), "Waiting for /path reference trajectory...");
        return;
    }

    // Fit track spline once per new path message
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
        mpc_controller::state x0;
        x0.x     = x_meas_;
        x0.y     = y_meas_;
        x0.theta = theta_meas_;
        x0.v     = v_meas_;
        x0.delta = delta_meas_;

        mpc_controller::MPCReturn result = mpc_->runMPC(x0);

        delta_dot_ = result.u0.delta_dot;
        a_         = result.u0.D_dot;

        integrationLayer();
        publishAckermannCommand();
        publishPredictedPath(result);

        if (csv_enabled_) writeCsvRow(x0, result);

        // Diagnostics at ~1 Hz
        static int log_count = 0;
        if (log_count++ % static_cast<int>(control_frequency_) == 0) {
            RCLCPP_INFO(get_logger(),
                "[MPC] meas: (x=%.2f, y=%.2f, θ=%.2f°, v=%.2f, δ=%.3f) "
                "cmd: (a=%.3f, δ̇=%.3f) ref: (v=%.2f, δ=%.3f) err=%.2fm t=%.1fms",
                x_meas_, y_meas_, theta_meas_ * 180.0 / M_PI, v_meas_, delta_meas_,
                a_, delta_dot_, v_ref_, delta_ref_,
                result.lateral_error, result.time_total * 1000.0);
        }

    } catch (const std::exception& e) {
        RCLCPP_ERROR(get_logger(), "MPC solve error: %s", e.what());
    }
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// INTEGRATION LAYER — convert MPC rate outputs to absolute reference commands
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::integrationLayer()
{
    delta_ref_ = std::clamp(delta_meas_ + delta_dot_ * control_dt_,
                            -max_steering_angle_, max_steering_angle_);
    v_ref_     = std::clamp(v_meas_     + a_          * control_dt_,
                            0.0, max_velocity_);
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// PUBLISH: Ackermann command
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::publishAckermannCommand()
{
    ackermann_msgs::msg::AckermannDriveStamped cmd;
    cmd.header.stamp                  = now();
    cmd.header.frame_id               = "base_link";
    cmd.drive.steering_angle          = delta_ref_;
    cmd.drive.steering_angle_velocity = std::abs(delta_dot_);
    cmd.drive.speed                   = v_ref_;
    cmd.drive.acceleration            = a_;
    ackermann_cmd_pub_->publish(cmd);
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// PUBLISH: MPC predicted horizon path
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::publishPredictedPath(const mpc_controller::MPCReturn& result)
{
    nav_msgs::msg::Path path;
    path.header.stamp    = now();
    path.header.frame_id = "map";
    for (const auto& opt : result.mpc_horizon) {
        geometry_msgs::msg::PoseStamped ps;
        ps.header = path.header;
        ps.pose.position.x = opt.xk.x;
        ps.pose.position.y = opt.xk.y;
        tf2::Quaternion q;
        q.setRPY(0, 0, opt.xk.theta);
        ps.pose.orientation = tf2::toMsg(q);
        path.poses.push_back(ps);
    }
    predicted_path_pub_->publish(path);
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// CSV LOGGER: find next trial number, create directory, open file
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::initCsvLogger(const std::string& lap_dir)
{
    // Create directory if it doesn't exist
    std::error_code ec;
    std::filesystem::create_directories(lap_dir, ec);
    if (ec) {
        RCLCPP_WARN(get_logger(), "Cannot create lap dir '%s': %s",
                    lap_dir.c_str(), ec.message().c_str());
        return;
    }

    // Find next available trial number — never overwrites an existing file
    int trial = 1;
    while (true) {
        std::string candidate = lap_dir + "/trial" + std::to_string(trial) + ".csv";
        struct stat st{};
        if (stat(candidate.c_str(), &st) != 0) break;
        ++trial;
    }
    csv_output_path_ = lap_dir + "/trial" + std::to_string(trial) + ".csv";

    csv_file_.open(csv_output_path_, std::ios::out | std::ios::trunc);
    if (!csv_file_.is_open()) {
        RCLCPP_WARN(get_logger(), "Cannot open CSV log: %s", csv_output_path_.c_str());
        return;
    }
    csv_file_ << "time_s,x,y,theta_rad,v_ms,delta_rad,"
              << "acc_ms2,steering_cmd_rad,s_m,lateral_error_m,solve_time_ms\n";
    csv_open_ = true;
    RCLCPP_INFO(get_logger(), "MPC CSV logger → %s", csv_output_path_.c_str());
}

// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
// CSV LOGGER: write one row per control step
// ―――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
void MPCControllerNode::writeCsvRow(const mpc_controller::state& x0,
                                    const mpc_controller::MPCReturn& result)
{
    if (!csv_open_) return;
    csv_file_ << std::fixed << std::setprecision(6)
              << now().seconds()              << ","
              << x0.x                         << ","
              << x0.y                         << ","
              << x0.theta                     << ","
              << x0.v                         << ","
              << x0.delta                     << ","
              << result.u0.D_dot              << ","
              << result.u0.delta_dot          << ","
              << x0.s                         << ","
              << result.lateral_error         << ","
              << result.time_total * 1000.0   << "\n";
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
