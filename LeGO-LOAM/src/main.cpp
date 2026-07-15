#include "rclcpp/rclcpp.hpp"
#include "featureAssociation.h"
#include "imageProjection.h"
#include "mapOptimization.h"
#include "transformFusion.h"
#include "StatusPublisher.h"

int main(int argc, char** argv) {
  Channel<ProjectionOut> projection_out_channel(true);
  Channel<AssociationOut> association_out_channel(false);

  rclcpp::init(argc, argv);

  // Create a dedicated node for status publishing
  auto status_node = std::make_shared<rclcpp::Node>("legoloam_status_node");
  StatusPublisher status("/status/legoloam", status_node);
  status.starting();  // Publish "Starting" immediately

  // Create the LOAM processing nodes
  auto IP = std::make_shared<ImageProjection>("image_projection", projection_out_channel);
  auto FA = std::make_shared<FeatureAssociation>("feature_association", projection_out_channel, association_out_channel);
  auto MO = std::make_shared<MapOptimization>("map_optimization", association_out_channel);
  auto TF = std::make_shared<TransformFusion>("transform_fusion");

  RCLCPP_INFO(IP->get_logger(), "\033[1;32m---->\033[0m ImageProjection Started.");
  RCLCPP_INFO(FA->get_logger(), "\033[1;32m---->\033[0m FeatureAssociation Started.");
  RCLCPP_INFO(MO->get_logger(), "\033[1;32m---->\033[0m MapOptimization Started.");
  RCLCPP_INFO(TF->get_logger(), "\033[1;32m---->\033[0m TransformFusion Started.");

  status.ready();  // Publish "Ready" after setup

  // Add a timer to continuously publish "Running" status
  auto running_timer = status_node->create_wall_timer(
    std::chrono::milliseconds(50),  // ✅ Correct way for 0.1 seconds
    [&status]() {
      status.running();
    }
  );


  // Multi-threaded executor with 4 threads
  rclcpp::executors::MultiThreadedExecutor executor(rclcpp::ExecutorOptions(), 4);
  executor.add_node(IP);
  executor.add_node(FA);
  executor.add_node(MO);
  executor.add_node(TF);
  executor.add_node(status_node);  // Include status heartbeat node

  executor.spin();

  rclcpp::shutdown();
  return 0;
}