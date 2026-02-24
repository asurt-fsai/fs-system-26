#include "mpc_controller/mpc_controller_node.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include <geometry_msgs/msg/quaternion.hpp>

MPCControllerNode::MPCControllerNode()
    : Node("mpc_controller"),
      reference_index_(0),
      has_reference_path_(false) {
    
    RCLCPP_INFO(this->get_logger(), "MPC Controller Node initialized");
    
    // Initialize config
    config_.horizon = 10;
    config_.dt = 0.1;
    config_.wheelbase = 2.5;
    config_.initializeDefaults();
    
    // Initialize solver
    mpc_solver_ = std::make_unique<MPCSolver>(config_);
    
    // Initialize state
    current_state_ = Eigen::Vector4d::Zero();
    
    // Create publishers
    cmd_vel_pub_ = this->create_publisher<geometry_msgs::msg::Twist>(
        "/cmd_vel", rclcpp::QoS(10)
    );
    predicted_path_pub_ = this->create_publisher<nav_msgs::msg::Path>(
        "/mpc/predicted_path", rclcpp::QoS(10)
    );
    debug_pub_ = this->create_publisher<std_msgs::msg::Float32MultiArray>(
        "/mpc/debug", rclcpp::QoS(10)
    );
    
    // Create subscribers
    odom_sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
        "/odom", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::odomCallback, this, std::placeholders::_1)
    );
    
    reference_path_sub_ = this->create_subscription<nav_msgs::msg::Path>(
        "/reference_path", rclcpp::QoS(10),
        std::bind(&MPCControllerNode::pathCallback, this, std::placeholders::_1)
    );
    
    // Create control loop timer
    control_timer_ = this->create_wall_timer(
        std::chrono::milliseconds(static_cast<int>(config_.dt * 1000)),
        std::bind(&MPCControllerNode::controlLoop, this)
    );
}

void MPCControllerNode::odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg) {
    const auto& pos = msg->pose.pose.position;
    const auto& ori = msg->pose.pose.orientation;
    
    // Extract heading from quaternion
    tf2::Quaternion quat(ori.x, ori.y, ori.z, ori.w);
    tf2::Matrix3x3 m(quat);
    double roll, pitch, yaw;
    m.getRPY(roll, pitch, yaw);
    
    // State: [x, y, theta, delta] (delta=0 for now)
    current_state_ << pos.x, pos.y, yaw, 0.0;
}

void MPCControllerNode::pathCallback(const nav_msgs::msg::Path::SharedPtr msg) {
    if (msg->poses.size() > 0) {
        reference_path_ = *msg;
        reference_index_ = 0;
        has_reference_path_ = true;
    }
}

Eigen::MatrixXd MPCControllerNode::getReferenceTrajectory() const {
    if (!has_reference_path_) {
        // Default: stay at current position
        return Eigen::MatrixXd::Zero(config_.horizon + 1, 4)
            .rowwise() + current_state_.transpose();
    }
    
    Eigen::MatrixXd reference_traj(config_.horizon + 1, 4);
    
    for (int i = 0; i <= config_.horizon; ++i) {
        size_t idx = std::min(
            reference_index_ + i,
            reference_path_.poses.size() - 1
        );
        
        const auto& pose = reference_path_.poses[idx].pose;
        const auto& pos = pose.position;
        const auto& ori = pose.orientation;
        
        // Extract heading
        tf2::Quaternion quat(ori.x, ori.y, ori.z, ori.w);
        tf2::Matrix3x3 m(quat);
        double roll, pitch, yaw;
        m.getRPY(roll, pitch, yaw);
        
        reference_traj(i, 0) = pos.x;
        reference_traj(i, 1) = pos.y;
        reference_traj(i, 2) = yaw;
        reference_traj(i, 3) = 0.0;
    }
    
    return reference_traj;
}

void MPCControllerNode::controlLoop() {
    if (!has_reference_path_) {
        return;
    }
    
    // Get reference trajectory
    Eigen::MatrixXd reference_traj = getReferenceTrajectory();
    
    // Solve MPC
    try {
        Eigen::MatrixXd optimal_controls;
        Eigen::MatrixXd predicted_traj;
        
        auto info = mpc_solver_->solve(
            current_state_,
            reference_traj,
            optimal_controls,
            predicted_traj
        );
        
        // Get first control
        Eigen::Vector2d control = optimal_controls.row(0).transpose();
        double v = control(0);
        double delta_dot = control(1);
        
        // Publish control
        geometry_msgs::msg::Twist twist;
        twist.linear.x = v;
        twist.angular.z = delta_dot;
        cmd_vel_pub_->publish(twist);
        
        // Publish predicted trajectory
        publishPredictedPath(predicted_traj);
        
        // Publish debug info
        publishDebugInfo(info);
        
        // Update reference index
        if (reference_index_ < reference_path_.poses.size() - 1) {
            reference_index_++;
        }
        
    } catch (const std::exception& e) {
        RCLCPP_ERROR(this->get_logger(), "MPC solve failed: %s", e.what());
    }
}

void MPCControllerNode::publishPredictedPath(const Eigen::MatrixXd& trajectory) {
    nav_msgs::msg::Path path_msg;
    path_msg.header.frame_id = "map";
    path_msg.header.stamp = this->now();
    
    for (int i = 0; i < trajectory.rows(); ++i) {
        geometry_msgs::msg::PoseStamped pose_stamped;
        pose_stamped.header = path_msg.header;
        
        pose_stamped.pose.position.x = trajectory(i, 0);
        pose_stamped.pose.position.y = trajectory(i, 1);
        
        // Convert heading to quaternion
        tf2::Quaternion quat;
        quat.setRPY(0, 0, trajectory(i, 2));
        pose_stamped.pose.orientation = tf2::toMsg(quat);
        
        path_msg.poses.push_back(pose_stamped);
    }
    
    predicted_path_pub_->publish(path_msg);
}

void MPCControllerNode::publishDebugInfo(const MPCSolver::SolveInfo& info) {
    std_msgs::msg::Float32MultiArray debug_msg;
    debug_msg.data = {
        static_cast<float>(info.cost),
        static_cast<float>(info.iterations),
        info.success ? 1.0f : 0.0f
    };
    debug_pub_->publish(debug_msg);
}

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MPCControllerNode>());
    rclcpp::shutdown();
    return 0;
}
