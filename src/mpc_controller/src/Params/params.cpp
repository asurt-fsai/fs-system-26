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

// Must include json.hpp BEFORE params.h so that #define N 20 from config.h
// is not yet in scope when json.hpp's template<unsigned N> is parsed.
#include "nlohmann/json.hpp"
using json = nlohmann::json;

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
      control_vec(Eigen::Matrix<double, NU, 1>::Zero()),
      // Initialize normalization to identity (no scaling)
      norm_x(1.0), norm_y(1.0), norm_theta(1.0), norm_delta(1.0), norm_v(1.0),
      norm_a(1.0), norm_delta_dot(1.0),
      norm_vx(1.0), norm_vy(1.0), norm_r(1.0), norm_s(1.0) {
    
    std::cout << "Params initialized (all values must be loaded from JSON files)" << std::endl;
    std::cout << "  - State vector (NX=" << NX << "D) initialized to zero" << std::endl;
    std::cout << "  - Control vector (NU=" << NU << "D) initialized to zero" << std::endl;
}

///////////////////////////////////////////////////////////////////////////////
// Load Vehicle & Model Parameters from JSON File ////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadVehicleParams(std::string vehicle_and_model_file) {
    std::ifstream vehicle_file(vehicle_and_model_file);
    if (!vehicle_file.is_open()) {
        std::cerr << "Error: Could not open vehicle and model parameters file: " << vehicle_and_model_file << std::endl;
        return;
    }
    
    try {
        json j;
        vehicle_file >> j;
        
        // ===== MOTOR MODEL PARAMETERS =====
        if (j.contains("Bm1")) Bm1 = j["Bm1"];
        if (j.contains("Bm2")) Bm2 = j["Bm2"];
        if (j.contains("Bm3")) Bm3 = j["Bm3"];
        
        // ===== GEOMETRIC PARAMETERS =====
        if (j.contains("Lf")) Lf = j["Lf"];
        if (j.contains("Lr")) Lr = j["Lr"];
        if (j.contains("wheelbase")) wheelbase = j["wheelbase"];
        if (j.contains("L")) L = j["L"];
        
        // ===== TRACK PARAMETERS =====
        if (j.contains("r_inner")) r_inner = j["r_inner"];
        if (j.contains("r_outer")) r_outer = j["r_outer"];
        
        // ===== PHYSICAL CONSTANTS =====
        if (j.contains("g")) g = j["g"];
        
        // ===== MOTOR & LINEARIZATION CONSTANTS =====
        if (j.contains("throttle_max")) throttle_max = j["throttle_max"];
        if (j.contains("linearize_eps")) linearize_eps = j["linearize_eps"];
        
        // ===== MPC CONFIGURATION PARAMETERS =====
        if (j.contains("dt")) dt = j["dt"];
        if (j.contains("horizon")) horizon = j["horizon"];
        
        std::cout << "Loaded vehicle and model parameters from: " << vehicle_and_model_file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing vehicle and model parameters file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load Cost Parameters from JSON File ///////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadCostParams(std::string cost_file) {
    std::ifstream input_file(cost_file);
    if (!input_file.is_open()) {
        std::cerr << "Error: Could not open cost parameters file: " << cost_file << std::endl;
        return;
    }
    
    try {
        json j;
        input_file >> j;
        
        // ===== COST FUNCTION WEIGHTS =====
        if (j.contains("weight_state")) weight_state = j["weight_state"];
        if (j.contains("weight_control")) weight_control = j["weight_control"];
        if (j.contains("weight_slack")) weight_slack = j["weight_slack"];
        
        // ===== REFERENCE TRAJECTORY VALUES =====
        if (j.contains("ref_velocity")) ref_velocity = j["ref_velocity"];
        if (j.contains("ref_x")) ref_x = j["ref_x"];
        if (j.contains("ref_y")) ref_y = j["ref_y"];
        
        std::cout << "Loaded cost parameters from: " << cost_file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing cost parameters file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load All Constraints (Bounds) from JSON File ///////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadConstraints(std::string bounds_file) {
    std::ifstream input_file(bounds_file);
    if (!input_file.is_open()) {
        std::cerr << "Error: Could not open bounds/constraints file: " << bounds_file << std::endl;
        return;
    }
    
    try {
        json j;
        input_file >> j;
        
        // ===== STATE BOX CONSTRAINTS - POSITION BOUNDS =====
        if (j.contains("x_min")) x_min = j["x_min"];
        if (j.contains("x_max")) x_max = j["x_max"];
        if (j.contains("y_min")) y_min = j["y_min"];
        if (j.contains("y_max")) y_max = j["y_max"];
        
        // ===== STATE BOX CONSTRAINTS - HEADING ANGLE BOUNDS =====
        if (j.contains("theta_min")) theta_min = j["theta_min"];
        if (j.contains("theta_max")) theta_max = j["theta_max"];
        
        // ===== STATE BOX CONSTRAINTS - VELOCITY BOUNDS (Speed, NOT acceleration) =====
        if (j.contains("v_min")) v_min = j["v_min"];
        if (j.contains("v_max")) v_max = j["v_max"];
        
        // ===== STATE BOX CONSTRAINTS - STEERING ANGLE BOUNDS =====
        if (j.contains("delta_min")) delta_min = j["delta_min"];
        if (j.contains("delta_max")) delta_max = j["delta_max"];
        
        // ===== CONTROL BOX CONSTRAINTS - ACCELERATION BOUNDS =====
        if (j.contains("a_min")) a_min = j["a_min"];
        if (j.contains("a_max")) a_max = j["a_max"];
        
        // ===== CONTROL BOX CONSTRAINTS - STEERING RATE BOUNDS =====
        if (j.contains("delta_dot_min")) delta_dot_min = j["delta_dot_min"];
        if (j.contains("delta_dot_max")) delta_dot_max = j["delta_dot_max"];
        
        std::cout << "Loaded all bounds/constraints from: " << bounds_file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing bounds/constraints file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load Normalization Factors from JSON File /////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadNormalization(std::string normalization_file) {
    std::ifstream input_file(normalization_file);
    if (!input_file.is_open()) {
        std::cerr << "Warning: Could not open normalization file: " << normalization_file << std::endl;
        std::cerr << "Using default normalization factors (1.0 = no scaling)" << std::endl;
        return;
    }
    
    try {
        json j;
        input_file >> j;
        
        // Initialize all normalization factors to 1.0 (identity - no scaling)
        // This provides safe defaults in case any key is missing from the JSON file
        norm_x = 1.0; norm_y = 1.0; norm_theta = 1.0; norm_delta = 1.0; norm_v = 1.0;
        norm_a = 1.0; norm_delta_dot = 1.0;
        norm_vx = 1.0; norm_vy = 1.0; norm_r = 1.0; norm_s = 1.0;
        
        // ===== STATE NORMALIZATION FACTORS =====
        if (j.contains("state_normalization")) {
            auto& state_norm = j["state_normalization"];
            if (state_norm.contains("X")) norm_x = state_norm["X"];
            if (state_norm.contains("Y")) norm_y = state_norm["Y"];
            if (state_norm.contains("theta")) norm_theta = state_norm["theta"];
            if (state_norm.contains("delta")) norm_delta = state_norm["delta"];
            if (state_norm.contains("v")) norm_v = state_norm["v"];
        }
        
        // ===== CONTROL NORMALIZATION FACTORS =====
        if (j.contains("control_normalization")) {
            auto& control_norm = j["control_normalization"];
            if (control_norm.contains("a")) norm_a = control_norm["a"];
            if (control_norm.contains("delta_dot")) norm_delta_dot = control_norm["delta_dot"];
        }
        
        // ===== REFERENCE NORMALIZATION FACTORS =====
        if (j.contains("reference_normalization")) {
            auto& ref_norm = j["reference_normalization"];
            if (ref_norm.contains("Vx")) norm_vx = ref_norm["Vx"];
            if (ref_norm.contains("Vy")) norm_vy = ref_norm["Vy"];
            if (ref_norm.contains("r")) norm_r = ref_norm["r"];
            if (ref_norm.contains("s")) norm_s = ref_norm["s"];
        }
        
        std::cout << "Loaded normalization factors from: " << normalization_file << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing normalization file: " << e.what() << std::endl;
    }
}

///////////////////////////////////////////////////////////////////////////////
// Load All Parameters from Multiple JSON Files //////////////////////////////
///////////////////////////////////////////////////////////////////////////////
void Params::loadAll(std::string vehicle_and_model_file, std::string cost_parameters_file, 
                     std::string bounds_and_constraints_file, std::string normalization_file) {
    std::cout << "\n========== LOADING ALL PARAMETERS FROM JSON FILES (ONCE ONLY) ===========" << std::endl;
    
    // Step 1: Load vehicle geometry, motor model, and MPC config (dt, horizon) from model file
    loadVehicleParams(vehicle_and_model_file);
    
    // Step 2: Load cost function weights and reference values
    loadCostParams(cost_parameters_file);
    
    // Step 3: Load all state and control bounds/constraints
    loadConstraints(bounds_and_constraints_file);
    
    // Step 4: Load normalization factors for numerical stability
    loadNormalization(normalization_file);
    
    std::cout << "========== ALL PARAMETERS LOADED SUCCESSFULLY ===========\n" << std::endl;
    std::cout << "Summary:" << std::endl;
    std::cout << "  - Vehicle/Model: " << vehicle_and_model_file << " (includes dt=" << dt << ", horizon=" << horizon << ")" << std::endl;
    std::cout << "  - Cost Parameters: " << cost_parameters_file << std::endl;
    std::cout << "  - Bounds/Constraints: " << bounds_and_constraints_file << std::endl;
    std::cout << "  - Normalization: " << normalization_file << std::endl;
}

/*///////////////////////////////////////////////////////////////////////////////
// Utility Methods ///////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
int Params::getPredictionSize() const {
    return horizon;
}*/

}  // namespace mpc_controller
