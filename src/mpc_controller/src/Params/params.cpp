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

#include "params.h"
#include <fstream>
#include <iostream>

namespace mpc_controller {

///////////////////////////////////////////////////////////////////////////////
// Params Constructor ////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
Params::Params() 
    : Bm1(0), Bm2(0), Bm3(0), Lf(0), Lr(0), 
      wheelbase(0), L(0), r_inner(0), r_outer(0), g(9.81),
      weight_state(0), weight_control(0), weight_slack(0),
      ref_velocity(0), ref_x(0), ref_y(0),
      x_min(0), x_max(0), y_min(0), y_max(0),
      theta_min(0), theta_max(0),
      v_min(0), v_max(0), delta_min(0), delta_max(0),
      a_min(0), a_max(0), delta_dot_min(0), delta_dot_max(0),
      throttle_max(0),
      linearize_eps(0), dt(0), horizon(0),
      state_vec(Eigen::Matrix<double, NX, 1>::Zero()),
      control_vec(Eigen::Matrix<double, NU, 1>::Zero()) {
    
    std::cout << "Params initialized (all values must be loaded from JSON files)" << std::endl;
    std::cout << "  - State vector (NX=" << NX << "D) initialized to zero" << std::endl;
    std::cout << "  - Control vector (NU=" << NU << "D) initialized to zero" << std::endl;
}

///////////////////////////////////////////////////////////////////////////////
// Load Vehicle Parameters from JSON File ////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadVehicleParams(std::string file) {
    std::ifstream config_file(file);
    if (!config_file.is_open()) {
        std::cerr << "Error: Could not open vehicle params file: " << file << std::endl;
        return;
    }
    
    try {
        json j;
        config_file >> j;
        
        // Geometric parameters
        if (j.contains("Bm1")) Bm1 = j["Bm1"];
        if (j.contains("Bm2")) Bm2 = j["Bm2"];
        if (j.contains("Bm3")) Bm3 = j["Bm3"];
        
        if (j.contains("Lf")) Lf = j["Lf"];
        if (j.contains("Lr")) Lr = j["Lr"];
        if (j.contains("wheelbase")) wheelbase = j["wheelbase"];
        if (j.contains("L")) L = j["L"];
        
        // Track parameters
        if (j.contains("r_inner")) r_inner = j["r_inner"];
        if (j.contains("r_outer")) r_outer = j["r_outer"];
        
        // Physical constants
        if (j.contains("g")) g = j["g"];
        
        // Motor model constants (Bm1, Bm2, Bm3) for throttle to acceleration mapping are loaded above
        // These same values are used in the bicycle model dynamics
        if (j.contains("throttle_max")) throttle_max = j["throttle_max"];
        
        // Linearization constant
        if (j.contains("linearize_eps")) linearize_eps = j["linearize_eps"];
        
        std::cout << "Loaded vehicle parameters from: " << file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing vehicle params file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load Cost Parameters from JSON File ///////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadCostParams(std::string file) {
    std::ifstream config_file(file);
    if (!config_file.is_open()) {
        std::cerr << "Error: Could not open cost params file: " << file << std::endl;
        return;
    }
    
    try {
        json j;
        config_file >> j;
        
        // Cost function weights
        if (j.contains("weight_state")) weight_state = j["weight_state"];
        if (j.contains("weight_control")) weight_control = j["weight_control"];
        if (j.contains("weight_slack")) weight_slack = j["weight_slack"];
        
        // Reference trajectory values
        if (j.contains("ref_velocity")) ref_velocity = j["ref_velocity"];
        if (j.contains("ref_x")) ref_x = j["ref_x"];
        if (j.contains("ref_y")) ref_y = j["ref_y"];
        
        std::cout << "Loaded cost parameters from: " << file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing cost params file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load All Constraints from JSON File ///////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadConstraints(std::string file) {
    std::ifstream config_file(file);
    if (!config_file.is_open()) {
        std::cerr << "Error: Could not open constraints file: " << file << std::endl;
        return;
    }
    
    try {
        json j;
        config_file >> j;
        
        // ===== STATE BOX CONSTRAINTS (ALL from JSON) =====
        if (j.contains("x_min")) x_min = j["x_min"];
        if (j.contains("x_max")) x_max = j["x_max"];
        if (j.contains("y_min")) y_min = j["y_min"];
        if (j.contains("y_max")) y_max = j["y_max"];
        if (j.contains("theta_min")) theta_min = j["theta_min"];
        if (j.contains("theta_max")) theta_max = j["theta_max"];
        
        // CRITICAL: Velocity bounds (speed, NOT acceleration)
        if (j.contains("v_min")) v_min = j["v_min"];
        if (j.contains("v_max")) v_max = j["v_max"];
        
        if (j.contains("delta_min")) delta_min = j["delta_min"];
        if (j.contains("delta_max")) delta_max = j["delta_max"];
        
        // ===== CONTROL BOX CONSTRAINTS (ALL from JSON) =====
        if (j.contains("a_min")) a_min = j["a_min"];           // Acceleration min
        if (j.contains("a_max")) a_max = j["a_max"];           // Acceleration max
        if (j.contains("delta_dot_min")) delta_dot_min = j["delta_dot_min"];
        if (j.contains("delta_dot_max")) delta_dot_max = j["delta_dot_max"];
        
        std::cout << "Loaded all box constraints from: " << file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing constraints file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load MPC Config from JSON File ////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadMPCConfig(std::string file) {
    std::ifstream config_file(file);
    if (!config_file.is_open()) {
        std::cerr << "Error: Could not open MPC config file: " << file << std::endl;
        return;
    }
    
    try {
        json j;
        config_file >> j;
        
        // MPC algorithm parameters only
        if (j.contains("dt")) dt = j["dt"];
        if (j.contains("horizon")) horizon = j["horizon"];
        
        std::cout << "Loaded MPC configuration from: " << file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing MPC config file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load All Parameters from Multiple JSON Files //////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadAll(std::string vehicle_file, std::string cost_file, 
                     std::string constraints_file, std::string mpc_file) {
    std::cout << "\n========== LOADING ALL PARAMETERS FROM JSON FILES (ONCE ONLY) ==========" << std::endl;
    loadVehicleParams(vehicle_file);      // Loads geometry + motor coefficients + throttle_max + linearize_eps
    loadCostParams(cost_file);            // Loads cost function weights
    loadConstraints(constraints_file);    // Loads ALL box constraints
    loadMPCConfig(mpc_file);              // Loads dt and horizon
    std::cout << "========== ALL PARAMETERS LOADED SUCCESSFULLY ===========\n" << std::endl;
}

///////////////////////////////////////////////////////////////////////////////
// Utility Methods ///////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
int Params::getPredictionSize() const {
    return horizon;
}

}  // namespace mpc_controller
