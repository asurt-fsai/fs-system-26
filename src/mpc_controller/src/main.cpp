#include <nlohmann/json.hpp>
#include "Bicycle Model/bicycle_model.h"


using json = nlohmann::json;

int main(){
    using namespace mpc_controller;
    std::ifstream config_file("params/config.json");
    json config_json;
    config_file >> config_json;

    


}