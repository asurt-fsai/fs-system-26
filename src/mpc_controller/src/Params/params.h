///////////////////////////////////////////////////////////////////////////////
// Copyright 2026 FSAI Control Systems
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

#ifndef MPC_PARAMS_H
#define MPC_PARAMS_H

#include "../config.h"
#include "../types.h"
#include "nlohmann/json.hpp"
using json = nlohmann::json;

namespace mpc_controller{
    
    class Params {
    public:
        ///////////////////////////////////////////////////////////////////////////
        // Vehicle Physical Parameters ///////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        double Bm1;          // Motor model parameter 1
        double Bm2;          // Motor model parameter 2
        double Bm3;          // Motor model parameter 3
        double Lf;           // Distance from center of mass to front axle [m]
        double Lr;           // Distance from center of mass to rear axle [m]
        double wheelbase;    // Wheelbase of the vehicle [m]
        double L;            // Length of the vehicle [m]
        double r_inner;      // Inner radius of the track [m]
        double r_outer;      // Outer radius of the track [m]
        double g;            // Gravitational acceleration [m/s^2]

        ///////////////////////////////////////////////////////////////////////////
        // Cost Function Parameters //////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        double weight_state;     // Weight for state tracking error
        double weight_control;   // Weight for control effort
        double weight_slack;     // Weight for slack variables
        double ref_velocity;     // Reference velocity [m/s]
        double ref_x;            // Reference x position [m]
        double ref_y;            // Reference y position [m]

        ///////////////////////////////////////////////////////////////////////////
        // Box Constraints - State Bounds ////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        // Position bounds
        double x_min, x_max;                      // Position X bounds [m]
        double y_min, y_max;                      // Position Y bounds [m]
        
        // Heading angle bounds
        double theta_min, theta_max;              // Heading angle bounds [rad]
        
        // Velocity bounds (not acceleration!) - CRITICAL
        double v_min, v_max;                      // Forward velocity bounds [m/s]
        
        // Steering angle bounds
        double delta_min, delta_max;              // Steering angle bounds [rad]

        ///////////////////////////////////////////////////////////////////////////
        // Box Constraints - Control Input Bounds ///////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        double a_min, a_max;                      // Acceleration bounds [m/s²]
        double delta_dot_min, delta_dot_max;      // Steering rate bounds [rad/s]
        
        ///////////////////////////////////////////////////////////////////////////
        // Motor Model Constants /////////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        // Motor coefficients for throttle-to-acceleration: a = throttle * (Bm1 + Bm2*v - Bm3*v²)
        // Note: Bm1, Bm2, Bm3 are defined above in Vehicle Physical Parameters
        double throttle_max;                      // Maximum throttle magnitude [-1, 1]
        
        ///////////////////////////////////////////////////////////////////////////
        // Linearization Constants ///////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        double linearize_eps;                     // Perturbation for numerical differentiation

        ///////////////////////////////////////////////////////////////////////////
        // MPC Algorithm Parameters //////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        double dt;                                // Time step for discretization [s]
        int horizon;                              // Prediction horizon [steps]

        ///////////////////////////////////////////////////////////////////////////
        // Normalization Factors (for numerical stability) ///////////////////////
        ///////////////////////////////////////////////////////////////////////////
        // State normalization factors
        double norm_x;                            // Normalization factor for X position
        double norm_y;                            // Normalization factor for Y position
        double norm_theta;                        // Normalization factor for heading angle
        double norm_delta;                        // Normalization factor for steering angle
        double norm_v;                            // Normalization factor for velocity
        
        // Control normalization factors
        double norm_a;                            // Normalization factor for acceleration
        double norm_delta_dot;                    // Normalization factor for steering rate
        
        // Reference normalization factors
        double norm_vx;                           // Normalization factor for reference Vx
        double norm_vy;                           // Normalization factor for reference Vy
        double norm_r;                            // Normalization factor for reference r
        double norm_s;                            // Normalization factor for reference s

        ///////////////////////////////////////////////////////////////////////////
        // State and Control Vectors (MPC Dimensions) ///////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        Eigen::Matrix<double, NX, 1> state_vec;     // 5D state vector [x, y, theta, delta, v]
        Eigen::Matrix<double, NU, 1> control_vec;   // 2D control vector [a, delta_dot]
        
        ///////////////////////////////////////////////////////////////////////////
        // Constructors //////////////////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        Params();
        
        ///////////////////////////////////////////////////////////////////////////
        // Parameter Loading Methods /////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        /// Load vehicle geometry, motor model parameters, and MPC config (dt, horizon)
        void loadVehicleParams(std::string vehicle_and_model_file);
        
        /// Load cost function weights and reference trajectory values
        void loadCostParams(std::string cost_parameters_file);
        
        /// Load all state and control bounds/constraints from JSON
        void loadConstraints(std::string bounds_and_constraints_file);
        
        /// Load separate MPC config file (optional, if dt/horizon differ from model file)
        void loadMPCConfig(std::string mpc_config_file);
        
        /// Load normalization factors for numerical stability from JSON
        void loadNormalization(std::string normalization_file);
        
        /// Load all parameters from four separate JSON files (dt and horizon from vehicle file only)
        void loadAll(std::string vehicle_and_model_file, std::string cost_parameters_file, 
                    std::string bounds_and_constraints_file, std::string normalization_file);
        
        ///////////////////////////////////////////////////////////////////////////
        // Utility Methods ///////////////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        int getPredictionSize() const;
    };
        
}

#endif // MPC_PARAMS_H