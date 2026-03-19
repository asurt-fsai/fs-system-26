#pragma once

#include <Eigen/Dense>
#include <vector>
#include <iostream>
#include <fstream>
#include <math.h>
#include "../types.h"

/**
 * @brief MPC Configuration Parameters
 * Tunable parameters for the Model Predictive Controller
 */
class MPCConfig {
public:
    // Prediction horizon (number of control steps, default: 50)
    int horizon = 50;
    
    // Time step between prediction steps in seconds (default: 0.02s = 50 Hz)
    double dt = 0.02;
    
    // Vehicle wheelbase in meters (distance from rear to front axle)
    double wheelbase = 2.5;
    
    // State tracking cost matrix Q (4x4 diagonal)
    // Default diagonal: [1.0, 1.0, 10.0, 0.1] for [x, y, theta, delta]
    Eigen::MatrixXd Q;
    
    // Control effort cost matrix R (2x2 diagonal)
    // Default diagonal: [0.1, 0.5] for [v, delta_dot]
    Eigen::MatrixXd R;
    
    // Terminal state cost matrix (default: Q * 2.0)
    Eigen::MatrixXd Q_terminal;
    
    // Maximum velocity in m/s
    double v_max = 5.0;
    
    // Minimum velocity in m/s
    double v_min = 0;
    
    // Maximum steering angle in radians (±26° for FSAI 2026, set to ±30° for margin)
    double delta_max = M_PI / 6;
    
    // Maximum steering rate in rad/s (used for steering command smoothing)
    double delta_dot_max = M_PI / 3;
    
    // Initialize default weight matrices (Q, R, Q_terminal)
    void initializeDefaults();
    
    // Get state vector size (returns 4)
    int getStateSize() const { return 4; }
    
    // Get control input size (returns 2)
    int getInputSize() const { return 2; }
    
    // Get prediction trajectory size (returns horizon + 1)
    int getPredictionSize() const { return horizon + 1; }
};
