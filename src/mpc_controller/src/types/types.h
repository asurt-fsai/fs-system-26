#ifndef MPC_TYPES_H
#define MPC_TYPES_H

#include "../config/config.h"
namespace mpc_controller{
    /**
     * @brief Vehicle state (5D Kinematic Bicycle Model)
     * 
     * Used by MPC: [x, y, theta, delta, v]
     * Indices match config.h::StateInputIndexes
     */
    struct state{
        // ===== KINEMATIC STATE (Used by MPC) =====
        double x;          // Global X position [m]
        double y;          // Global Y position [m]
        double theta;      // Heading angle [rad], normalized to [-π, π]
        double delta;      // Steering angle [rad], constrained to ±0.6109 (±35°)
        double v;          // Forward velocity [m/s], constrained to [0, 25] for FSAI

        // ===== AUXILIARY FIELDS (Not used in MPC dynamics, kept for compatibility) =====
        // These are used by other parts of the system (path tracking, visualization, etc.)
        double vx;         // Longitudinal velocity (body frame) - NOT used in MPC
        double vy;         // Lateral velocity (body frame) - NOT used in MPC
        double r;          // Yaw rate [rad/s] - NOT used in MPC (use dtheta/dt instead)
        double s;          // Arc length along track - for path projection only
        double Throttle;   // Throttle command [-1, 1] - auxiliary, not a dynamics state

        void setZero(){
            x = 0.0;
            y = 0.0;
            vx = 0.0;
            vy = 0.0;
            theta = 0.0;
            r = 0.0;
            delta = 0.0;
            v = 0.0;
            s = 0.0;
            Throttle = 0.0;
        }
        void unwrapTheta(){
            if (theta > M_PI) {
                theta -= 2 * M_PI;
            } else if (theta < -M_PI) {
                theta += 2 * M_PI;
            }
        }
        void unwrapS(double track_length){
            if (s > track_length) {
                s -= track_length;
            } else if (s < 0) {
                s += track_length;
            }
        }
    };

    /**
     * @brief Vehicle control input (2D)
     * 
     * Control semantics: ACCELERATION-BASED
     * MPC directly commands acceleration (m/s²)
     * Constraints: -5.0 ≤ a ≤ 5.0 m/s²
     */
    struct control{
        double D_dot;      // Acceleration [m/s²] (CLARIFIED: NOT velocity, NOT throttle)
        double delta_dot;  // Steering angle rate [rad/s]
        double dV_ghost;   // Ghost velocity rate (auxiliary, not dynamics state)

        void setZero(){
            D_dot = 0.0;
            delta_dot = 0.0;
            dV_ghost = 0.0;
        }
    };
    
    struct PathToJson{
        // a struct to hold the paths to the json files for model parameters, bounds, costs, and normalization parameters
        const std::string model_path;
        const std::string bounds_path;
        const std::string costs_path;
        const std::string normalization_path;
    };

    // StateVector: NX=5 states [x, y, theta, delta, v] (matches bicycle model)
    typedef Eigen::Matrix<double, NX, 1> StateVector;
    // ControlVector: NU=2 inputs [acceleration, steering_rate]
    typedef Eigen::Matrix<double, NU, 1> ControlVector;
    typedef Eigen::Matrix<double, NX, 1> state_MPC;    // 5D MPC state vector [x, y, theta, delta, v]

    typedef Eigen::Matrix<double, NX, 1> state_Bounds;
    typedef Eigen::Matrix<double, NU, 1> control_Bounds;

    // ===== MPC Cost Matrix Type Definitions =====
    typedef Eigen::Matrix<double, NX, NX> Q_MPC;       // State cost matrix (NX x NX)
    typedef Eigen::Matrix<double, NX, 1> q_MPC;        // State cost vector (NX x 1)
    typedef Eigen::Matrix<double, NU, NU> R_MPC;       // Control cost matrix (NU x NU)
    typedef Eigen::Matrix<double, NU, 1> r_MPC;        // Control cost vector (NU x 1)
    typedef Eigen::Matrix<double, NX, NU> S_MPC;       // Cross term cost matrix (NX x NU)

    // ===== State Index Constants =====
    static constexpr int STATE_INDEX_THETA = 2;        // Index of theta in state vector
    static constexpr int STATE_INDEX_VELOCITY = 4;     // Index of v in state vector

    StateVector StateToVector(const state& X);
    inline state_MPC stateToVector(const state& X) {
        state_MPC vec;
        vec << X.x, X.y, X.theta, X.delta, X.v;
        return vec;
    }
    ControlVector ControlToVector(const control& U);

    state VectorToState(const StateVector& X_vec);
    control VectorToControl(const ControlVector& U_vec);

}
#endif //MPC_TYPES_H