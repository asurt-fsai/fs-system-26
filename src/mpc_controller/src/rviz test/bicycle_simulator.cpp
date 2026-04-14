#include "bicycle_simulator.h"
#include <fstream>
#include <sstream>
#include <algorithm>

// ─────────────────────────────────────────────────────────────────────────────
BicycleSimulator::BicycleSimulator()
    : Node("bicycle_simulator")
{
    /* ─── Parameters ──────────────────────────────────────────────────── */
    declare_parameter("wheelbase",       wheelbase_);
    declare_parameter("sim_dt",          sim_dt_);
    declare_parameter("v_max",           v_max_);
    declare_parameter("delta_max",       delta_max_);
    declare_parameter("track_a",         track_a_);
    declare_parameter("track_b",         track_b_);
    declare_parameter("track_n",         track_n_);
    declare_parameter("initial_v",       v_);
    declare_parameter("initial_x",       x_);
    declare_parameter("initial_y",       y_);
    declare_parameter("initial_theta",   theta_);
    declare_parameter("track_csv_path",  std::string(""));

    wheelbase_       = get_parameter("wheelbase").as_double();
    sim_dt_          = get_parameter("sim_dt").as_double();
    v_max_           = get_parameter("v_max").as_double();
    delta_max_       = get_parameter("delta_max").as_double();
    track_a_         = get_parameter("track_a").as_double();
    track_b_         = get_parameter("track_b").as_double();
    track_n_         = get_parameter("track_n").as_int();
    v_               = get_parameter("initial_v").as_double();
    x_               = get_parameter("initial_x").as_double();
    y_               = get_parameter("initial_y").as_double();
    theta_           = get_parameter("initial_theta").as_double();
    track_csv_path_  = get_parameter("track_csv_path").as_string();

    /* ─── Load or generate track ──────────────────────────────────────── */
    if (!track_csv_path_.empty()) {
        if (loadTrackCSV(track_csv_path_)) {
            RCLCPP_INFO(get_logger(),
                "Loaded track from CSV: %s  (%zu waypoints)",
                track_csv_path_.c_str(), track_points_.size());

            // Place car at the first waypoint, heading toward second
            if (track_points_.size() >= 2) {
                x_ = track_points_[0].first;
                y_ = track_points_[0].second;
                double dx = track_points_[1].first  - track_points_[0].first;
                double dy = track_points_[1].second - track_points_[0].second;
                theta_ = std::atan2(dy, dx);
            }
        } else {
            RCLCPP_WARN(get_logger(),
                "Failed to load CSV '%s' — falling back to oval track",
                track_csv_path_.c_str());
            track_csv_path_.clear();
            generateOvalTrack();
        }
    } else {
        generateOvalTrack();
    }

    /* ─── Subscribers ─────────────────────────────────────────────────── */
    cmd_sub_ = create_subscription<geometry_msgs::msg::Twist>(
        "/cmd_vel", 10,
        std::bind(&BicycleSimulator::cmdVelCallback, this, std::placeholders::_1));

    /* ─── Publishers ──────────────────────────────────────────────────── */
    odom_pub_  = create_publisher<nav_msgs::msg::Odometry>("/odom", 10);
    track_pub_ = create_publisher<nav_msgs::msg::Path>(
        "/reference_path", rclcpp::QoS(10).transient_local());

    /* ─── Timers ──────────────────────────────────────────────────────── */
    auto sim_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::duration<double>(sim_dt_));
    sim_timer_ = create_wall_timer(sim_ns,
        std::bind(&BicycleSimulator::simStep, this));

    // Publish track immediately then periodically (every 2 s) for late-joining subscribers
    publishTrack();
    track_timer_ = create_wall_timer(
        std::chrono::seconds(2),
        [this]() { publishTrack(); });

    RCLCPP_INFO(get_logger(),
        "Bicycle Simulator started  dt=%.4fs  wheelbase=%.2fm  x0=(%.1f,%.1f) θ0=%.2f",
        sim_dt_, wheelbase_, x_, y_, theta_);
}

// ─────────────────────────────────────────────────────────────────────────────
void BicycleSimulator::cmdVelCallback(
    const geometry_msgs::msg::Twist::SharedPtr msg)
{
    cmd_accel_       = msg->linear.x;   // acceleration [m/s²]
    cmd_delta_target_ = msg->angular.z;  // target steering angle [rad]
}

// ─────────────────────────────────────────────────────────────────────────────
// RK4 integration of the kinematic bicycle model
// The MPC controller sends acceleration + target steering angle.
// The simulator acts as a steering position servo: it computes the steering
// rate required to track the target and integrates the full 5-state bicycle
// model.  This matches how IPG CarMaker applies steering — a low-level
// actuator tracks the commanded angle.
// ─────────────────────────────────────────────────────────────────────────────
void BicycleSimulator::simStep()
{
    // Compute steering rate to servo toward the target angle
    // Use a fast first-order response: δ̇ = (δ_target − δ) / τ, clamped
    constexpr double tau = 0.02;  // servo time constant [s]
    double delta_rate = (cmd_delta_target_ - delta_) / tau;
    constexpr double delta_dot_max = 3.0;  // [rad/s] fast actuator
    delta_rate = std::clamp(delta_rate, -delta_dot_max, delta_dot_max);

    auto f = [this](double th, double d, double v,
                    double a, double dd)
        -> std::array<double, 5>
    {
        return {
            v * std::cos(th),
            v * std::sin(th),
            (v / wheelbase_) * std::tan(d),
            dd,
            a
        };
    };

    // RK4 sub-steps
    auto k1 = f(theta_, delta_, v_, cmd_accel_, delta_rate);

    double th2 = theta_ + 0.5 * sim_dt_ * k1[2];
    double d2  = delta_ + 0.5 * sim_dt_ * k1[3];
    double v2  = v_     + 0.5 * sim_dt_ * k1[4];
    auto k2 = f(th2, d2, v2, cmd_accel_, delta_rate);

    double th3 = theta_ + 0.5 * sim_dt_ * k2[2];
    double d3  = delta_ + 0.5 * sim_dt_ * k2[3];
    double v3  = v_     + 0.5 * sim_dt_ * k2[4];
    auto k3 = f(th3, d3, v3, cmd_accel_, delta_rate);

    double th4 = theta_ + sim_dt_ * k3[2];
    double d4  = delta_ + sim_dt_ * k3[3];
    double v4  = v_     + sim_dt_ * k3[4];
    auto k4 = f(th4, d4, v4, cmd_accel_, delta_rate);

    x_     += (sim_dt_ / 6.0) * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0]);
    y_     += (sim_dt_ / 6.0) * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1]);
    theta_ += (sim_dt_ / 6.0) * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2]);
    delta_ += (sim_dt_ / 6.0) * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3]);
    v_     += (sim_dt_ / 6.0) * (k1[4] + 2*k2[4] + 2*k3[4] + k4[4]);

    // Clamp
    delta_ = std::clamp(delta_, -delta_max_, delta_max_);
    v_     = std::clamp(v_, 0.0, v_max_);

    publishOdom();
}

// ─────────────────────────────────────────────────────────────────────────────
void BicycleSimulator::publishOdom()
{
    nav_msgs::msg::Odometry odom;
    odom.header.stamp    = now();
    odom.header.frame_id = "map";
    odom.child_frame_id  = "base_link";

    odom.pose.pose.position.x = x_;
    odom.pose.pose.position.y = y_;
    odom.pose.pose.position.z = 0.0;

    tf2::Quaternion q;
    q.setRPY(0, 0, theta_);
    odom.pose.pose.orientation = tf2::toMsg(q);

    odom.twist.twist.linear.x  = v_;
    odom.twist.twist.linear.y  = delta_;   // pass steering angle to MPC
    odom.twist.twist.angular.z = (v_ / wheelbase_) * std::tan(delta_);

    odom_pub_->publish(odom);
}

// ─────────────────────────────────────────────────────────────────────────────
// Load a CSV track file (x,y per line, no header)
// ─────────────────────────────────────────────────────────────────────────────
bool BicycleSimulator::loadTrackCSV(const std::string& csv_path)
{
    std::ifstream file(csv_path);
    if (!file.is_open()) {
        RCLCPP_ERROR(get_logger(), "Cannot open track CSV: %s", csv_path.c_str());
        return false;
    }

    track_points_.clear();
    std::string line;
    while (std::getline(file, line)) {
        // Skip empty lines and comment lines
        if (line.empty() || line[0] == '#') continue;

        std::istringstream ss(line);
        double x_val, y_val;
        char comma;
        if (ss >> x_val >> comma >> y_val) {
            track_points_.emplace_back(x_val, y_val);
        }
    }

    // Close the loop: if first and last points are within 1m, append the first point
    if (track_points_.size() >= 3) {
        double dx = track_points_.front().first  - track_points_.back().first;
        double dy = track_points_.front().second - track_points_.back().second;
        if (std::sqrt(dx*dx + dy*dy) < 5.0) {
            track_points_.push_back(track_points_.front());
        }
    }

    return track_points_.size() >= 2;
}

// ─────────────────────────────────────────────────────────────────────────────
// Generate a parametric oval track as fallback
// ─────────────────────────────────────────────────────────────────────────────
void BicycleSimulator::generateOvalTrack()
{
    track_points_.clear();
    track_points_.reserve(track_n_);
    for (int i = 0; i < track_n_; ++i) {
        double t = 2.0 * M_PI * static_cast<double>(i) / track_n_;
        track_points_.emplace_back(track_a_ * std::cos(t),
                                   track_b_ * std::sin(t));
    }
    RCLCPP_INFO(get_logger(), "Generated oval track: %.0f × %.0f m, %d pts",
                track_a_, track_b_, track_n_);
}

// ─────────────────────────────────────────────────────────────────────────────
// Publish the track as a nav_msgs/Path with tangent headings
// ─────────────────────────────────────────────────────────────────────────────
void BicycleSimulator::publishTrack()
{
    if (track_points_.empty()) return;

    nav_msgs::msg::Path path;
    path.header.stamp    = now();
    path.header.frame_id = "map";

    const size_t n = track_points_.size();
    for (size_t i = 0; i < n; ++i) {
        geometry_msgs::msg::PoseStamped ps;
        ps.header = path.header;
        ps.pose.position.x = track_points_[i].first;
        ps.pose.position.y = track_points_[i].second;
        ps.pose.position.z = 0.0;

        // Tangent heading (central difference, wrapping around for closed tracks)
        size_t i_next = (i + 1) % n;
        size_t i_prev = (i == 0) ? n - 1 : i - 1;
        double dx = track_points_[i_next].first  - track_points_[i_prev].first;
        double dy = track_points_[i_next].second - track_points_[i_prev].second;
        tf2::Quaternion q;
        q.setRPY(0, 0, std::atan2(dy, dx));
        ps.pose.orientation = tf2::toMsg(q);

        path.poses.push_back(ps);
    }

    track_pub_->publish(path);
    RCLCPP_INFO(get_logger(), "Published track with %zu waypoints", n);
}

// ─────────────────────────────────────────────────────────────────────────────
int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<BicycleSimulator>());
    rclcpp::shutdown();
    return 0;
}
