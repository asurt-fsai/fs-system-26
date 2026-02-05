#include <memory>
#include <vector>
#include <iostream>

#include "rclcpp/rclcpp.hpp"
#include "zed_msgs/msg/objects_stamped.hpp" // Adapting to the ZED format

using std::placeholders::_1;

class PerceptionListener : public rclcpp::Node
{
public:
    PerceptionListener() : Node("perception_listener")
    {
        // 1. Subscribe to the ZED Topic from your bag file
        // Check 'ros2 bag info' to confirm this topic name matches exactly
        std::string topic_name = "/perception";
        
        subscription_ = this->create_subscription<zed_msgs::msg::ObjectsStamped>(
            topic_name, 
            10, 
            std::bind(&PerceptionListener::topic_callback, this, _1));

        RCLCPP_INFO(this->get_logger(), "--- SLAM Listener Started ---");
        RCLCPP_INFO(this->get_logger(), "Listening to: %s", topic_name.c_str());
        RCLCPP_INFO(this->get_logger(), "Waiting for bag file playback...");
    }

private:
    void topic_callback(const zed_msgs::msg::ObjectsStamped::SharedPtr msg) const
    {
        if (msg->objects.empty()) {
            return; 
        }

        // Loop through the detected objects
        for (const auto& obj : msg->objects) {
            
            // Extract Position
            double x = obj.position[0];
            double y = obj.position[1];
            double z = obj.position[2]; // Now used below
            
            int id = obj.label_id;      
            std::string class_type = obj.label; // FIXED: Changed int to string
            float confidence = obj.confidence;

            // Alert / Print to Terminal
            if (confidence > 50.0) { 
                RCLCPP_INFO(this->get_logger(), 
                    "[ALERT] %s Detected! ID: %d | Conf: %.1f | Pos: [%.2f, %.2f, %.2f]", 
                    class_type.c_str(), // Prints "Cone" (or whatever label ZED gives)
                    id, 
                    confidence,
                    x, y, z);
            }
        }
    }

    rclcpp::Subscription<zed_msgs::msg::ObjectsStamped>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PerceptionListener>());
    rclcpp::shutdown();
    return 0;
}