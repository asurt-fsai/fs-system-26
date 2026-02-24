#pragma once

#include <Eigen/Dense>
#include <vector>
#include <iostream>
#include <fstream>
#include <math.h>

/**
 * @file config.h
 * @brief MPC Configuration Management
 * 
 * This file defines all tunable parameters for the Model Predictive Controller.
 * These parameters control the vehicle dynamics model, optimization horizon,
 * cost function weights, and constraint limits.
 * 
 * All parameters are tunable at runtime via the setWeights() function,
 * enabling online parameter adjustment during vehicle testing.
 * 
 * FSAI 2026 USAGE:
 * - Modify these values based on vehicle track test results
 * - Use ROS 2 parameter server to change values without rebuilding
 * - Test different tuning scenarios (tight turns vs straight-line acceleration)
 */
class MPCConfig {
public:
    // ============================================================================
    // PREDICTION HORIZON AND SAMPLING
    // ============================================================================
    
    /**
     * @brief Prediction horizon length (number of control steps to optimize)
     * 
     * Default: 50 steps
     * At 50 Hz control rate: 50 * 0.02s = 1.0 second lookahead
     * 
     * TUNING GUIDANCE:
     * - Larger horizon (80-100): More predictive, smoother but slower computation
     * - Smaller horizon (30-40): Reactive, faster computation but less predictive
     * - FSAI 2026: Start with 50, adjust based on track complexity
     */
    int horizon = 50;
    
    /**
     * @brief Time step between prediction steps (seconds)
     * 
     * Default: 0.02s (50 Hz control loop frequency)
     * 
     * Must match your ROS 2 control node update rate:
     * - Hardware execution frequency: 1/dt Hz
     * - If running at 50 Hz: dt = 0.02
     * - If running at 100 Hz: dt = 0.01
     * 
     * CRITICAL: Keep synchronized with actual control loop execution!
     */
    double dt = 0.02;
    
    // ============================================================================
    // VEHICLE DYNAMICS MODEL PARAMETERS
    // ============================================================================
    
    /**
     * @brief Vehicle wheelbase (distance from front axle to rear axle)
     * 
     * Default: 2.5 meters
     * Unit: meters
     * 
     * FORMULA STUDENT VEHICLES (FSAI 2026):
     * - Typical FS car: 1.5-2.5 meters
     * - Larger car: ~2.5m
     * - Smaller car: ~1.6m
     * 
     * USED IN: Kinematic bicycle model
     * dtheta/dt = (v / wheelbase) * tan(delta)
     * 
     * TO MEASURE: Distance from rear axle center to front axle center
     * 
     * IMPACT ON MPC:
     * - Wrong value → incorrect turning rate prediction
     * - Underestimated → oversteer prediction (too sharp turns)
     * - Overestimated → understeer prediction (too gentle turns)
     */
    double wheelbase = 2.5;
    
    // ============================================================================
    // COST FUNCTION WEIGHTS (Q, R matrices)
    // ============================================================================
    
    /**
     * @brief State tracking cost matrix Q (4x4 diagonal)
     * 
     * Penalizes deviation from reference trajectory during prediction horizon.
     * Diagonal elements: [q_x, q_y, q_theta, q_delta]
     * 
     * OPTIMIZATION OBJECTIVE:
     * Cost = Σ||x_i - x_ref_i||²_Q + ||u_i||²_R + ||x_final||²_Q_terminal
     * 
     * Default values:
     * Q(0,0) = 1.0   : Position X error penalty
     * Q(1,1) = 1.0   : Position Y error penalty
     * Q(2,2) = 10.0  : Heading angle error penalty (LARGE - critical for track following)
     * Q(3,3) = 0.1   : Steering angle error penalty (small)
     * 
     * TUNING FOR FSAI 2026:
     * - Increase heading (Q(2,2)): Better line tracking, more aggressive steering
     * - Decrease heading (Q(2,2)): Smoother control, more robust to disturbances
     * - Increase position (Q(0,0), Q(1,1)): Tighter lateral control
     * - Increase steering angle (Q(3,3)): Penalty for extreme steering angles
     * 
     * PHYSICAL INTERPRETATION:
     * Each unit of weight ≈ importance of that error metric in the cost function
     * Weight of 10x means this error is 10x more important than a weight of 1x
     */
    Eigen::MatrixXd Q;
    
    /**
     * @brief Control effort cost matrix R (2x2 diagonal)
     * 
     * Penalizes large control inputs to promote smooth, energy-efficient control.
     * Diagonal elements: [r_v, r_delta_dot]
     * 
     * Default values:
     * R(0,0) = 0.1   : Velocity change penalty (smooth acceleration/braking)
     * R(1,1) = 0.5   : Steering rate penalty (smooth steering)
     * 
     * EFFECT OF R:
     * - Large R: Smooth, conservative control (good for sensor stability)
     * - Small R: Aggressive, fast control (good for tight handling)
     * 
     * TUNING FOR FSAI 2026:
     * - For smooth acceleration zones: R(0,0) = 0.1-0.5 (smoother)
     * - For aggressive handling: R(0,0) = 0.01-0.1 (faster response)
     * - Steering rate: Usually R(1,1) > R(0,0) (steering smoother than acceleration)
     * 
     * WHY SMOOTH CONTROL MATTERS:
     * - Prevents sensor vibration (IMU, cameras)
     * - Reduces tire slip and improves traction
     * - Prevents servo saturation (mechanical limits)
     * - Improves energy efficiency (less tire heating)
     */
    Eigen::MatrixXd R;
    
    /**
     * @brief Terminal state cost matrix Q_terminal (4x4 diagonal)
     * 
     * Additional penalty on the state at the END of the prediction horizon.
     * Ensures the MPC plans to reach the target trajectory precisely,
     * not just within the horizon.
     * 
     * Default: Q_terminal = Q * 2.0 (typically 2-5x the stage cost)
     * 
     * WHY TERMINAL COST:
     * Without terminal cost:
     *   MPC might optimize well for steps 0-40, but not care about step 50
     * With terminal cost:
     *   MPC ensures good tracking all the way to end of horizon
     * 
     * TUNING:
     * - Larger terminal weight: Stronger final position enforcement
     * - Smaller terminal weight: More freedom in final steps
     * - For FSAI 2026: Keep at Q*2.0 to ensure smooth handoff to next planning cycle
     */
    Eigen::MatrixXd Q_terminal;
    
    // ============================================================================
    // CONSTRAINT LIMITS (Vehicle physical and safety limits)
    // ============================================================================
    
    /**
     * @brief Maximum velocity (m/s)
     * 
     * Default: 2.0 m/s (~7.2 km/h)
     * 
     * FSAI 2026 TYPICAL VALUES:
     * - Low speed testing: 2-3 m/s
     * - Medium speed: 4-6 m/s
     * - High speed: 8-12 m/s
     * 
     * SET TO YOUR VEHICLE'S CAPABILITIES:
     * - Motor max RPM → wheel circumference → v_max
     * - E.g., 2000 RPM, 0.6m wheel circumference → ~20 m/s theoretical max
     * 
     * SAFETY CONSIDERATIONS:
     * - Conservative testing: Start with 50% of max capability
     * - Gradually increase as confidence improves
     * - Always check battery voltage (reduces max power at low voltage)
     */
    double v_max = 2.0;
    
    /**
     * @brief Minimum velocity (m/s)
     * 
     * Default: 0.0 m/s (can stop)
     * 
     * For most FS cars: Keep at 0.0 to allow full stop
     * Only increase if your drivetrain cannot maintain very low speeds
     */
    double v_min = 0;
    
    /**
     * @brief Maximum steering angle (radians)
     * 
     * Default: π/6 = 30 degrees (0.524 radians)
     * 
     * FSAI 2026 CALIBRATION:
     * - The steering angle is +- 26 degrees for the FSAI 2026 car, so we set it to 30 degrees for a safety margin.
     * - Measure your steering system's physical limit
     * - FS cars typically: ±25 to ±35 degrees
     * - Formula Electric cars: ±20 to ±25 degrees
     * - Account for servo mechanical limits, not just geometry
     * 
     * FORMULA: delta_max_rad = (degrees * π) / 180
     * Examples:
     * - 30° = 30 * π / 180 = 0.524 rad
     * - 25° = 25 * π / 180 = 0.436 rad
     * - 35° = 35 * π / 180 = 0.611 rad
     * 
     * IMPACT:
     * - Too low: Vehicle can't turn tight enough (undershoot trajectory)
     * - Too high: Unrealistic commands sent to steering servo
     */
    double delta_max = M_PI / 6;
    
    /**
     * @brief Maximum steering rate (radians/second)
     * 
     * this will be used later for smoothing the steering commands and ensuring we don't command the servo to change too quickly.
     * Default: π/3 = 60 degrees/second (1.047 rad/s)
     * 
     * FSAI 2026 CALIBRATION:
     * - Depends on steering servo speed and ratio
     * - Typical servo: 0.1-0.2 seconds to move full range
     * - E.g., 30° range in 0.15s → 200°/s → 3.49 rad/s
     * 
     * FORMULA: delta_dot_max_rad_s = (degrees_per_sec * π) / 180
     * 
     * MECHANICAL LIMITS TO CHECK:
     * - Servo response time (typically 0.1-0.3 seconds for FS)
     * - Steering linkage stiffness
     * - Wheel alignment compliance
     * 
     * TUNING FOR FSAI 2026:
     * - Test: Send maximum steering command, measure actual steering rate
     * - Use slightly lower than measured max for safety margin
     * - Example: If servo does ±90°/s, use ±80°/s in controller
     */
    double delta_dot_max = M_PI / 3;
    
    // ============================================================================
    // PUBLIC METHODS
    // ============================================================================
    
    /**
     * @brief Initialize default weight matrices
     * 
     * Populates Q, R, and Q_terminal with sensible defaults for FS vehicles.
     * Called by MPCSolver constructor.
     * 
     * DEFAULT VALUES SET:
     * - Q diagonal: [1.0, 1.0, 10.0, 0.1]
     * - R diagonal: [0.1, 0.5]
     * - Q_terminal = Q * 2.0
     * 
     * USAGE:
     * 1. Create config (automatically uses defaults from member initializers)
     * 2. Call initializeDefaults() to fill weight matrices
     * 3. Override with online tuning if needed
     * 
     * For FSAI 2026 Competition:
     * - Use initializeDefaults() for first track test
     * - Record results and adjust Q/R based on performance
     * - Store best tuning for each track section
     */
    void initializeDefaults();
    
    /**
     * @brief Get state vector dimensionality
     * 
     * @return 4 (state = [x, y, theta, delta])
     * 
     * Used internally for matrix sizing.
     * State dimension never changes in this implementation.
     */
    int getStateSize() const { return 4; }
    
    /**
     * @brief Get control input dimensionality
     * 
     * @return 2 (control = [v, delta_dot])
     * 
     * Used internally for matrix sizing.
     * Control dimension never changes in this implementation.
     */
    int getInputSize() const { return 2; }
    
    /**
     * @brief Get prediction trajectory size
     * 
     * @return horizon + 1
     * 
     * Trajectory includes initial state (step 0) plus all predicted steps.
     * Example: horizon=50 → trajectory size = 51 states
     * 
     * Used for allocating trajectory matrices in solver.
     */
    int getPredictionSize() const { return horizon + 1; }
};
