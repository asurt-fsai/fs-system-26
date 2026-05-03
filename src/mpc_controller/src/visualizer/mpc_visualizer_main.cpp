// Standalone entry point for the MPC Visualizer node
// Used by both the IPG launch file and the RViz-test launch file.
#include "mpc_visualizer.h"

int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MPCVisualizer>());
    rclcpp::shutdown();
    return 0;
}
