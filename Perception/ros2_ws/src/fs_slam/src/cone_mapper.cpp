#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include "fs_slam/msg/cone_array.hpp"

using std::placeholders::_1;

class ConeMapper : public rclcpp::Node {
    public:
    ConeMapper() : Node("cone_mapper"){
        tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
        tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

        //subscriber (from perception)
        subscription_ = this->create_subscription<fs_slam::msg::ConeArray>(
            "perception/cones", 10, std::bind(&ConeMapper::perception_callback, this, _1));

        //Publisher (to Path planning) [A map]
        map_publisher_ = this->create_publisher<visualization_msgs::msg::MarkerArray>(
            "slam/global_map", 10);

        RCLCPP_INFO(this->get_logger(), "SLAM Mapping Node Started");
    }
    private:
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
    std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
    rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr map_publisher_;
    
    rclcpp::Subscription<fs_slam::msg::ConeArray>::SharedPtr subscription_;


    //The magic happens here
    void perception_callback(const fs_slam::msg::ConeArray::SharedPtr msg){
        geometry_msgs::msg::TransformStamped t;
        try{
            t = tf_buffer_->lookupTransform("map", "base_link", msg->header.stamp, rclcpp::Duration::from_seconds(0.1));
        }
        catch(const tf2::TransformException & ex){
            RCLCPP_WARN(this->get_logger(), "Could not transform: %s", ex.what());
            return;
        }
        //Process cones
        int count = msg->cones.size();
        RCLCPP_INFO(this->get_logger(), "Recieved %d cone data, tranform valid!", count);


    }
};

int main(int argc, char * argv[]){
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ConeMapper>());
    rclcpp::shutdown();
    return 0;
}