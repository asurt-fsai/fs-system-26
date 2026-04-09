#include <nlohmann/json.hpp>
#include "Bicycle Model/bicycle_model.h"
#include "Params/params.h"
#include "Constraints/constraints.h"
#include "Cost/Cost.h"
#include <iostream>
#include <fstream>

using json = nlohmann::json;

int main(){
    using namespace mpc_controller;
    
    try {
        ///////////////////////////////////////////////////////////////////////////
        // Step 1: Load Configuration File Paths /////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        std::cout << "Loading configuration..." << std::endl;
        
        std::ifstream config_file("src/mpc_controller/src/Params/config.json");
        if (!config_file.is_open()) {
            std::cerr << "Error: Could not open config.json" << std::endl;
            return 1;
        }
        
        json config_json;
        config_file >> config_json;
        
        // Extract all 5 file paths from config.json
        std::string vehicle_file = config_json["vehicle_file"];
        std::string cost_file = config_json["cost_file"];
        std::string constraints_file = config_json["constraints_file"];
        std::string motor_file = config_json["motor_file"];
        std::string mpc_file = config_json["mpc_file"];
        
        std::cout << "Configuration loaded successfully" << std::endl;
        
        ///////////////////////////////////////////////////////////////////////////
        // Step 2: Initialize Params with Loaded Paths ///////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        std::cout << "Initializing parameters..." << std::endl;
        
        Params params;
        params.loadAll(vehicle_file, cost_file, constraints_file, mpc_file);
        
        std::cout << "Parameters initialized successfully" << std::endl;
        
        ///////////////////////////////////////////////////////////////////////////
        // Step 3: Create Control System Components //////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        std::cout << "Creating control system components..." << std::endl;
        
        // Create constraint checker
        ConstraintSet constraints(params);
        
        // Create cost function
        Cost cost(params);
        
        // Create bicycle model with loaded parameters
        BicycleModel model(params);
        
        std::cout << "Control system components created successfully" << std::endl;
        
        ///////////////////////////////////////////////////////////////////////////
        // Step 4: Main Control Loop /////////////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////
        std::cout << "Starting main control loop..." << std::endl;
        
        // TODO: Implement main control loop
        // - Read sensor data
        // - Compute MPC solution
        // - Execute control commands
        // - Repeat
        
        std::cout << "Application terminated successfully" << std::endl;
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
}