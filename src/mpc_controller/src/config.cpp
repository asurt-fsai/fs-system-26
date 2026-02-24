#include "config.h"



// Initialize MPC cost function weight matrices
void MPCConfig::initializeDefaults() {
    // Q matrix: state tracking weights [x, y, theta, delta]
    Q = Eigen::MatrixXd::Zero(4, 4);
    // just some inital values to start with, these will be tuned based on performance on the track
    Q(0, 0) = 1.0;   // X position error (lane keeping)
    Q(1, 1) = 1.0;   // Y position error (distance along track)
    Q(2, 2) = 10.0;  // Heading angle error (most critical)
    Q(3, 3) = 0.1;   // Steering angle error (least critical)
    
    // R matrix: control effort weights [velocity_change, steering_rate]
    R = Eigen::Matrix2d::Zero();
    
    R(0, 0) = 0.1;   // Velocity change penalty
    R(1, 1) = 0.5;   // Steering rate penalty (5x heavier than velocity)
    
    // Terminal cost: additional penalty at end of prediction horizon
    Q_terminal = Q * 2.0;
}
