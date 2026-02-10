#include <memory>
#include <vector>
#include <iostream>

#include "rclcpp/rclcpp.hpp"
#include "asurt_msgs/msg/landmark_array.hpp"

using std::placeholders::_1;

class PerceptionListener : public rclcpp::Node
{
public:
    PerceptionListener() : Node("perception_listener")
    {
        // Subscribe to the perception landmarks topic produced by the conversion node
        std::string topic_name = "/perception_landmarks";

        subscription_ = this->create_subscription<asurt_msgs::msg::LandmarkArray>(
            topic_name,
            10,
            std::bind(&PerceptionListener::topic_callback, this, _1));

        RCLCPP_INFO(this->get_logger(), "--- SLAM Listener Started ---");
        RCLCPP_INFO(this->get_logger(), "Listening to: %s", topic_name.c_str());
        RCLCPP_INFO(this->get_logger(), "Waiting for bag file playback...");
    }

private:
    void topic_callback(const asurt_msgs::msg::LandmarkArray::SharedPtr msg) const
    {
        if (msg->landmarks.empty()) {
            return;
        }

        // Loop through the converted landmarks
        for (const auto & lm : msg->landmarks) {
            double x = lm.position.x;
            double y = lm.position.y;
            double z = lm.position.z;

            int id = lm.identifier;
            uint32_t type = lm.type;
            double probability = lm.probability * 100.0; // report as percent

            if (probability > 50.0) {
                RCLCPP_INFO(this->get_logger(),
                    "[ALERT] Landmark type:%u ID:%d | Prob: %.1f%% | Pos: [%.2f, %.2f, %.2f]",
                    type,
                    id,
                    probability,
                    x, y, z);
            }
        }
    }

    rclcpp::Subscription<asurt_msgs::msg::LandmarkArray>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PerceptionListener>());
    rclcpp::shutdown();
    return 0;
}